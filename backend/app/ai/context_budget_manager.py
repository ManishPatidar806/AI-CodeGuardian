import math
from dataclasses import dataclass, field
from typing import Sequence

import structlog

from app.repository_analysis.models import CodeChunk
from app.retrieval.hybrid_retriever import (
    RepositoryContext,
    RetrievalResult,
    StructuralContext,
)

logger = structlog.get_logger(__name__)


class TokenCounter:
    """Estimates and manages token counts for LLM prompt context budgeting.

    Uses `tiktoken` if available; otherwise falls back to a precise character-heuristic
    estimator (~4.0 characters per token for source code and English text).
    """

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        """Initialize TokenCounter with optional tiktoken encoding.

        Args:
            encoding_name: Name of the tiktoken encoding model.
        """
        self.encoding_name = encoding_name
        self._encoder = None

        try:
            import tiktoken  # type: ignore

            self._encoder = tiktoken.get_encoding(encoding_name)
        except ImportError:
            logger.debug(
                "tiktoken_not_installed",
                fallback="character_heuristic_estimator",
            )

    def count_tokens(self, text: str | None) -> int:
        """Count or estimate the number of tokens in the given text.

        Args:
            text: Input string.

        Returns:
            Estimated token count.
        """
        if not text:
            return 0

        if self._encoder is not None:
            try:
                return len(self._encoder.encode(text))
            except Exception as e:
                logger.warning("tiktoken_encoding_error", error=str(e))

        # Fallback heuristic: ~3.8 characters per token for source code & markdown
        return math.ceil(len(text) / 3.8)

    def truncate_to_tokens(self, text: str, max_tokens: int) -> tuple[str, bool]:
        """Truncate text cleanly at line boundaries so it fits within max_tokens.

        Args:
            text: Input text string.
            max_tokens: Maximum allowed token budget.

        Returns:
            Tuple of (truncated_text, is_truncated_flag).
        """
        if not text or max_tokens <= 0:
            return "", True

        current_tokens = self.count_tokens(text)
        if current_tokens <= max_tokens:
            return text, False

        lines = text.splitlines(keepends=True)
        accumulated_lines: list[str] = []
        accumulated_tokens = 0

        for line in lines:
            line_tokens = self.count_tokens(line)
            if accumulated_tokens + line_tokens > max_tokens:
                break
            accumulated_lines.append(line)
            accumulated_tokens += line_tokens

        truncated_text = "".join(accumulated_lines).rstrip()
        if not truncated_text and lines:
            # If a single line exceeds max_tokens, slice character-wise safely
            target_chars = max(1, int(max_tokens * 3.5))
            truncated_text = lines[0][:target_chars]

        return truncated_text + "\n... [TRUNCATED DUE TO CONTEXT BUDGET]", True


@dataclass(frozen=True)
class ContextBudget:
    """Defines token budget allocation quotas for prompt context components.

    Attributes:
        max_total_tokens: Total maximum allowable tokens for prompt context.
        prompt_overhead_tokens: Reserved tokens for prompt templates & system instructions.
        diff_share_pct: Share percentage allocated to changed git diff (Priority 1).
        semantic_share_pct: Share percentage allocated to semantic RAG results (Priority 2).
        dependency_share_pct: Share percentage allocated to structural/dependency results (Priority 3).
        summary_share_pct: Share percentage allocated to project summary (Priority 4).
    """

    max_total_tokens: int = 8192
    prompt_overhead_tokens: int = 1000
    diff_share_pct: float = 0.45
    semantic_share_pct: float = 0.25
    dependency_share_pct: float = 0.20
    summary_share_pct: float = 0.10

    @property
    def net_context_tokens(self) -> int:
        """Net tokens available for dynamic context assembly."""
        return max(0, self.max_total_tokens - self.prompt_overhead_tokens)


@dataclass
class BudgetContextResult:
    """Container returned by ContextBudgetManager detailing assembled context and token statistics.

    Attributes:
        formatted_context: Cleanly formatted, budgeted context string ready for LLM input.
        total_tokens: Total estimated tokens consumed by context string.
        diff_tokens: Tokens consumed by changed git diff section.
        semantic_tokens: Tokens consumed by semantic retrieval section.
        dependency_tokens: Tokens consumed by structural/dependency section.
        summary_tokens: Tokens consumed by project summary section.
        truncated_sections: List of sections that were truncated to fit budget.
        budget_utilization_pct: Percentage of net context budget utilized.
    """

    formatted_context: str
    total_tokens: int
    diff_tokens: int
    semantic_tokens: int
    dependency_tokens: int
    summary_tokens: int
    truncated_sections: list[str] = field(default_factory=list)
    budget_utilization_pct: float = 0.0


class ContextBudgetManager:
    """Manages context budgeting, token counting, chunk truncation, and prioritized allocation.

    The ContextBudgetManager forms Phase 4 of the AI CodeGuardian pipeline.
    It guarantees that assembled prompt contexts never exceed LLM token limits while
    strictly prioritizing:
    1. Changed Git Diff (Highest priority - primary review subject)
    2. Semantic RAG Code Snippets (2nd priority - contextual relevance)
    3. Structural / Dependency Context (3rd priority - call graph & imports)
    4. Project Summary (4th priority - high-level overview)

    Features dynamic cascading reallocation: unused tokens from higher-priority tiers
    cascade down to lower-priority tiers automatically.
    """

    def __init__(
        self,
        token_counter: TokenCounter | None = None,
        budget: ContextBudget | None = None,
    ) -> None:
        """Initialize ContextBudgetManager.

        Args:
            token_counter: Optional TokenCounter instance.
            budget: Optional ContextBudget configuration.
        """
        self.token_counter = token_counter or TokenCounter()
        self.budget = budget or ContextBudget()

    def build_budgeted_context(
        self,
        diff: str,
        semantic_results: Sequence[RetrievalResult] | None = None,
        structural_results: Sequence[StructuralContext] | None = None,
        project_summary: str | None = None,
        repository_context: RepositoryContext | None = None,
        custom_max_tokens: int | None = None,
    ) -> BudgetContextResult:
        """Assemble a context string strictly budgeted within token limits using prioritized cascade allocation.

        Args:
            diff: Unified git diff string (Priority 1).
            semantic_results: Optional sequence of semantic retrieval results (Priority 2).
            structural_results: Optional sequence of structural contexts (Priority 3).
            project_summary: Optional project summary overview string (Priority 4).
            repository_context: Optional RepositoryContext object (supplies semantic/structural if provided).
            custom_max_tokens: Optional override for max total token limit.

        Returns:
            BudgetContextResult containing formatted context string and detailed token metrics.
        """
        net_budget = (
            max(0, custom_max_tokens - self.budget.prompt_overhead_tokens)
            if custom_max_tokens is not None
            else self.budget.net_context_tokens
        )

        logger.info(
            "context_budgeting_started",
            net_budget_tokens=net_budget,
            diff_length=len(diff or ""),
        )

        # Merge RepositoryContext if passed
        if repository_context:
            semantic_results = semantic_results or repository_context.semantic_results
            structural_results = (
                structural_results or repository_context.structural_results
            )

        raw_semantic = list(semantic_results or [])
        raw_structural = list(structural_results or [])

        # Base token allocations for each priority tier
        diff_quota = int(net_budget * self.budget.diff_share_pct)
        semantic_quota = int(net_budget * self.budget.semantic_share_pct)
        dependency_quota = int(net_budget * self.budget.dependency_share_pct)
        summary_quota = int(net_budget * self.budget.summary_share_pct)

        cascade_pool = 0
        truncated_sections: list[str] = []

        # -------------------------------------------------------------
        # Tier 1 (Priority 1): Changed Git Diff
        # -------------------------------------------------------------
        diff_str = (diff or "").strip()
        diff_tokens_raw = self.token_counter.count_tokens(diff_str)

        if diff_tokens_raw <= diff_quota:
            budgeted_diff = diff_str
            diff_tokens = diff_tokens_raw
            cascade_pool += diff_quota - diff_tokens_raw
        else:
            budgeted_diff, was_trunc = self.token_counter.truncate_to_tokens(
                diff_str, diff_quota
            )
            diff_tokens = self.token_counter.count_tokens(budgeted_diff)
            if was_trunc:
                truncated_sections.append("git_diff")

        # -------------------------------------------------------------
        # Tier 2 (Priority 2): Semantic Retrieval Results
        # -------------------------------------------------------------
        available_semantic_budget = semantic_quota + cascade_pool
        budgeted_semantic_text, semantic_tokens, sem_was_trunc, sem_unused = (
            self._budget_semantic_results(raw_semantic, available_semantic_budget)
        )
        cascade_pool = sem_unused
        if sem_was_trunc:
            truncated_sections.append("semantic_retrieval")

        # -------------------------------------------------------------
        # Tier 3 (Priority 3): Dependency / Structural Context
        # -------------------------------------------------------------
        available_dep_budget = dependency_quota + cascade_pool
        budgeted_dep_text, dep_tokens, dep_was_trunc, dep_unused = (
            self._budget_structural_results(raw_structural, available_dep_budget)
        )
        cascade_pool = dep_unused
        if dep_was_trunc:
            truncated_sections.append("dependency_retrieval")

        # -------------------------------------------------------------
        # Tier 4 (Priority 4): Project Summary Overview
        # -------------------------------------------------------------
        available_summary_budget = summary_quota + cascade_pool
        summary_str = (project_summary or "").strip()
        summary_tokens_raw = self.token_counter.count_tokens(summary_str)

        if summary_tokens_raw <= available_summary_budget:
            budgeted_summary = summary_str
            summary_tokens = summary_tokens_raw
        else:
            budgeted_summary, sum_was_trunc = self.token_counter.truncate_to_tokens(
                summary_str, available_summary_budget
            )
            summary_tokens = self.token_counter.count_tokens(budgeted_summary)
            if sum_was_trunc:
                truncated_sections.append("project_summary")

        # -------------------------------------------------------------
        # Final Context Assembly
        # -------------------------------------------------------------
        context_parts: list[str] = []

        if budgeted_diff:
            context_parts.append(
                f"=== CHANGED GIT DIFF (P1) ===\n```diff\n{budgeted_diff}\n```"
            )

        if budgeted_semantic_text:
            context_parts.append(
                f"=== SEMANTICALLY RELATED CODE (P2) ===\n{budgeted_semantic_text}"
            )

        if budgeted_dep_text:
            context_parts.append(
                f"=== DEPENDENCY & STRUCTURAL CONTEXT (P3) ===\n{budgeted_dep_text}"
            )

        if budgeted_summary:
            context_parts.append(
                f"=== PROJECT ARCHITECTURE SUMMARY (P4) ===\n{budgeted_summary}"
            )

        formatted_context = "\n\n".join(context_parts)
        total_tokens = self.token_counter.count_tokens(formatted_context)
        utilization_pct = (
            round((total_tokens / net_budget) * 100.0, 2) if net_budget > 0 else 0.0
        )

        logger.info(
            "context_budgeting_completed",
            total_tokens=total_tokens,
            net_budget=net_budget,
            utilization_pct=utilization_pct,
            truncated_sections=truncated_sections,
        )

        return BudgetContextResult(
            formatted_context=formatted_context,
            total_tokens=total_tokens,
            diff_tokens=diff_tokens,
            semantic_tokens=semantic_tokens,
            dependency_tokens=dep_tokens,
            summary_tokens=summary_tokens,
            truncated_sections=truncated_sections,
            budget_utilization_pct=utilization_pct,
        )

    def _budget_semantic_results(
        self,
        results: list[RetrievalResult],
        max_budget: int,
    ) -> tuple[str, int, bool, int]:
        """Budget and format semantic retrieval results up to max_budget.

        Returns:
            Tuple of (formatted_text, consumed_tokens, is_truncated, remaining_unused_tokens).
        """
        if not results or max_budget <= 0:
            return "", 0, False, max(0, max_budget)

        formatted_snippets: list[str] = []
        current_tokens = 0
        was_truncated = False

        for res in results:
            snippet = self._format_code_block(
                file_path=res.file_path,
                symbol=res.symbol_name,
                start_line=res.start_line,
                end_line=res.end_line,
                content=res.content,
            )
            snippet_tokens = self.token_counter.count_tokens(snippet)

            if current_tokens + snippet_tokens <= max_budget:
                formatted_snippets.append(snippet)
                current_tokens += snippet_tokens
            else:
                # Truncate partial snippet if budget allows
                remaining_tokens = max_budget - current_tokens
                if remaining_tokens > 100:
                    trunc_snippet, _ = self.token_counter.truncate_to_tokens(
                        snippet, remaining_tokens
                    )
                    formatted_snippets.append(trunc_snippet)
                    current_tokens += self.token_counter.count_tokens(trunc_snippet)
                was_truncated = True
                break

        unused_tokens = max(0, max_budget - current_tokens)
        return (
            "\n\n".join(formatted_snippets),
            current_tokens,
            was_truncated,
            unused_tokens,
        )

    def _budget_structural_results(
        self,
        results: list[StructuralContext],
        max_budget: int,
    ) -> tuple[str, int, bool, int]:
        """Budget and format structural dependency contexts up to max_budget.

        Returns:
            Tuple of (formatted_text, consumed_tokens, is_truncated, remaining_unused_tokens).
        """
        if not results or max_budget <= 0:
            return "", 0, False, max(0, max_budget)

        formatted_sections: list[str] = []
        current_tokens = 0
        was_truncated = False

        for struct_res in results:
            header = f"Related File: {struct_res.file_path} (Relationship: {struct_res.relationship})"
            header_tokens = self.token_counter.count_tokens(header)

            if current_tokens + header_tokens > max_budget:
                was_truncated = True
                break

            chunk_texts: list[str] = []
            section_tokens = header_tokens

            for chunk in struct_res.chunks:
                chunk_str = self._format_chunk(chunk)
                ct_tokens = self.token_counter.count_tokens(chunk_str)

                if current_tokens + section_tokens + ct_tokens <= max_budget:
                    chunk_texts.append(chunk_str)
                    section_tokens += ct_tokens
                else:
                    was_truncated = True
                    break

            if chunk_texts or section_tokens > 0:
                combined_section = header + "\n" + "\n".join(chunk_texts)
                formatted_sections.append(combined_section)
                current_tokens += self.token_counter.count_tokens(combined_section)

            if was_truncated:
                break

        unused_tokens = max(0, max_budget - current_tokens)
        return (
            "\n\n".join(formatted_sections),
            current_tokens,
            was_truncated,
            unused_tokens,
        )

    @staticmethod
    def _format_code_block(
        file_path: str,
        symbol: str | None,
        start_line: int | None,
        end_line: int | None,
        content: str,
    ) -> str:
        symbol_info = f" | Symbol: {symbol}" if symbol else ""
        line_info = (
            f" | Lines: {start_line}-{end_line}"
            if start_line and end_line
            else ""
        )
        return f"File: `{file_path}`{symbol_info}{line_info}\n```text\n{content}\n```"

    @staticmethod
    def _format_chunk(chunk: CodeChunk) -> str:
        symbol_info = f" | Symbol: {chunk.symbol_name}" if chunk.symbol_name else ""
        line_info = (
            f" | Lines: {chunk.start_line}-{chunk.end_line}"
            if chunk.start_line and chunk.end_line
            else ""
        )
        return f"Chunk File: `{chunk.file_path}`{symbol_info}{line_info}\n```text\n{chunk.content}\n```"
