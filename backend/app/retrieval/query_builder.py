import re
from dataclasses import dataclass, field
from typing import Sequence

import structlog

from app.review_engine.context import ReviewContext

logger = structlog.get_logger(__name__)

# Stopwords commonly found in git diffs and natural language text that do not aid code retrieval
STOPWORDS: set[str] = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
    "the",
    "this",
    "diff",
    "git",
    "index",
    "plus",
    "minus",
    "file",
    "files",
    "none",
    "true",
    "false",
    "null",
}

# Regex patterns to detect code symbols in diff additions (+) across Python, JS/TS, Go, Java, C++
SYMBOL_PATTERNS: list[re.Pattern[str]] = [
    # Python / JS function or method definitions
    re.compile(r"^\+\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.MULTILINE),
    # Class definitions
    re.compile(r"^\+\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.MULTILINE),
    # JS/TS function / const function definitions
    re.compile(
        r"^\+\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        re.MULTILINE,
    ),
    re.compile(
        r"^\+\s*(?:export\s+)?const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:async\s*)?\(",
        re.MULTILINE,
    ),
    # Go function / method definitions
    re.compile(
        r"^\+\s*func\s+(?:\([^)]+\)\s+)?([a-zA-Z_][a-zA-Z0-9_]*)", re.MULTILINE
    ),
    # Java / C++ method signatures
    re.compile(
        r"^\+\s*(?:public|private|protected|static|final|native|synchronized|\s)*[a-zA-Z0-9_<>\[\]]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
        re.MULTILINE,
    ),
    # Imports & dependencies
    re.compile(
        r"^\+\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)", re.MULTILINE
    ),
]


@dataclass(frozen=True)
class GeneratedQueries:
    """Encapsulates automatically generated retrieval queries and extracted code metadata.

    Attributes:
        primary_query: Comprehensive single query synthesized for vector retrieval.
        domain_query: Query capturing high-level intent from MR title, description, and branch.
        symbol_query: Query capturing specific code symbols (classes, functions, methods).
        diff_query: Query capturing changed keywords and diff context.
        extracted_symbols: List of code symbols identified in changed files and diff.
        keywords: Unique set of extracted domain and code keywords.
    """

    primary_query: str
    domain_query: str
    symbol_query: str
    diff_query: str
    extracted_symbols: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


class QueryBuilder:
    """Automatically constructs semantic retrieval queries from MR metadata and diff artifacts.

    The QueryBuilder forms Phase 3 of the AI CodeGuardian pipeline.
    It eliminates manual query drafting by analyzing:
    - MR Title & Description
    - Source & Target Branch Names
    - Commit Messages
    - Changed Files List
    - Git Diff Hunks and AST Symbols

    The resulting queries are optimized for ChromaDB / SemanticRetriever vector searches.
    """

    def __init__(self, max_query_length: int = 1000) -> None:
        """Initialize QueryBuilder.

        Args:
            max_query_length: Maximum character length for primary synthesized query.
        """
        self.max_query_length = max_query_length

    def build_queries(
        self,
        title: str,
        description: str | None = None,
        changed_files: Sequence[str] | None = None,
        git_diff: str | None = None,
        branch_name: str | None = None,
        commit_messages: Sequence[str] | str | None = None,
    ) -> GeneratedQueries:
        """Construct multi-perspective retrieval queries from MR inputs.

        Args:
            title: MR Title.
            description: Optional MR Description.
            changed_files: Optional sequence of changed file paths.
            git_diff: Optional git diff string.
            branch_name: Optional source branch name.
            commit_messages: Optional sequence or string of commit messages.

        Returns:
            GeneratedQueries object containing primary, domain, symbol, and diff queries.
        """
        logger.debug(
            "query_building_started",
            title=title,
            branch=branch_name,
            changed_files_count=len(changed_files or []),
            diff_length=len(git_diff or ""),
        )

        # 1. Extract domain keywords from Title, Description, Branch, Commit messages
        domain_tokens = self._extract_domain_keywords(
            title=title,
            description=description,
            branch_name=branch_name,
            commit_messages=commit_messages,
        )

        # 2. Extract code symbols (classes, functions, methods, modules) from diff & changed files
        symbols = self._extract_code_symbols(
            git_diff=git_diff or "",
            changed_files=changed_files or [],
        )

        # 3. Extract key terms from changed diff hunks
        diff_tokens = self._extract_diff_keywords(git_diff or "")

        # 4. Extract file path keywords
        file_path_tokens = self._extract_file_path_keywords(changed_files or [])

        # 5. Build specialized query representations
        domain_query = " ".join(domain_tokens)
        symbol_query = " ".join(symbols)
        diff_query = " ".join(diff_tokens)

        # 6. Combine all tokens for primary synthesized query
        all_unique_keywords = self._deduplicate_tokens(
            domain_tokens + symbols + file_path_tokens + diff_tokens
        )

        primary_query = " ".join(all_unique_keywords)
        if len(primary_query) > self.max_query_length:
            primary_query = primary_query[: self.max_query_length].rsplit(" ", 1)[0]

        logger.info(
            "query_building_completed",
            primary_query_length=len(primary_query),
            symbols_found=len(symbols),
            keywords_count=len(all_unique_keywords),
        )

        return GeneratedQueries(
            primary_query=primary_query,
            domain_query=domain_query,
            symbol_query=symbol_query,
            diff_query=diff_query,
            extracted_symbols=symbols,
            keywords=all_unique_keywords,
        )

    def build_from_context(self, context: ReviewContext) -> GeneratedQueries:
        """Convenience method to construct queries directly from a ReviewContext object.

        Args:
            context: ReviewContext instance containing project, MR iid, title, diffs, etc.

        Returns:
            GeneratedQueries result.
        """
        # Aggregate commit messages
        commit_msgs: list[str] = []
        for commit in context.commits or []:
            msg = commit.get("message") or commit.get("title")
            if msg:
                commit_msgs.append(str(msg))

        # Aggregate diff strings and changed files
        diff_chunks: list[str] = []
        changed_files: list[str] = []
        for diff_entry in context.diffs or []:
            diff_str = diff_entry.get("diff") or ""
            new_path = diff_entry.get("new_path") or diff_entry.get("old_path")
            if diff_str:
                diff_chunks.append(diff_str)
            if new_path:
                changed_files.append(new_path)

        combined_diff = "\n".join(diff_chunks)

        return self.build_queries(
            title=context.title,
            description=context.description,
            changed_files=changed_files,
            git_diff=combined_diff,
            branch_name=context.source_branch,
            commit_messages=commit_msgs,
        )

    def build_unified_query(
        self,
        title: str,
        description: str | None = None,
        changed_files: Sequence[str] | None = None,
        git_diff: str | None = None,
        branch_name: str | None = None,
        commit_messages: Sequence[str] | str | None = None,
    ) -> str:
        """Returns a single consolidated retrieval query string.

        Args:
            title: MR Title.
            description: Optional Description.
            changed_files: Optional list of changed files.
            git_diff: Optional Git diff.
            branch_name: Optional Branch name.
            commit_messages: Optional Commit messages.

        Returns:
            Unified query string.
        """
        queries = self.build_queries(
            title=title,
            description=description,
            changed_files=changed_files,
            git_diff=git_diff,
            branch_name=branch_name,
            commit_messages=commit_messages,
        )
        return queries.primary_query

    def _extract_domain_keywords(
        self,
        title: str,
        description: str | None,
        branch_name: str | None,
        commit_messages: Sequence[str] | str | None,
    ) -> list[str]:
        """Extract domain concepts and key terms from text metadata.

        Args:
            title: MR Title.
            description: MR Description.
            branch_name: Branch name.
            commit_messages: Commit message(s).

        Returns:
            List of extracted domain tokens.
        """
        raw_text_parts: list[str] = [title]
        if description:
            raw_text_parts.append(description)

        if branch_name:
            # Clean branch delimiters like feature/jira-123-add-auth -> feature jira 123 add auth
            cleaned_branch = re.sub(r"[/_\-\.]", " ", branch_name)
            raw_text_parts.append(cleaned_branch)

        if commit_messages:
            if isinstance(commit_messages, str):
                raw_text_parts.append(commit_messages)
            else:
                raw_text_parts.extend(commit_messages)

        full_text = " ".join(raw_text_parts)
        return self._tokenize_and_clean(full_text)

    def _extract_code_symbols(
        self,
        git_diff: str,
        changed_files: Sequence[str],
    ) -> list[str]:
        """Extract modified function, class, and method names from git diff additions.

        Args:
            git_diff: Raw git diff text.
            changed_files: List of file paths.

        Returns:
            List of unique code symbol names.
        """
        symbols: list[str] = []

        if git_diff:
            for pattern in SYMBOL_PATTERNS:
                matches = pattern.findall(git_diff)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    cleaned_symbol = match.strip()
                    if cleaned_symbol and len(cleaned_symbol) > 2:
                        symbols.append(cleaned_symbol)

        # Extract symbols from file path basenames (e.g. user_service.py -> UserService)
        for path in changed_files:
            basename = path.rsplit("/", 1)[-1].split(".")[0]
            tokens = self._tokenize_identifier(basename)
            symbols.extend(tokens)

        return self._deduplicate_tokens(symbols)

    def _extract_diff_keywords(self, git_diff: str) -> list[str]:
        """Extract meaningful code tokens from added diff lines (+).

        Args:
            git_diff: Raw git diff text.

        Returns:
            List of code tokens.
        """
        if not git_diff:
            return []

        added_lines: list[str] = []
        for line in git_diff.splitlines():
            # Only consider added lines (+) excluding diff header +++
            if line.startswith("+") and not line.startswith("+++"):
                # Strip leading + and indentation
                clean_line = line[1:].strip()
                # Ignore comments or trivial lines
                if clean_line and not clean_line.startswith(("#", "//", "/*", "*")):
                    added_lines.append(clean_line)

        combined_added_code = " ".join(added_lines)
        return self._tokenize_and_clean(combined_added_code, min_length=3)[:30]

    def _extract_file_path_keywords(self, changed_files: Sequence[str]) -> list[str]:
        """Extract folder and file component tokens from changed file paths.

        Args:
            changed_files: Sequence of file paths.

        Returns:
            List of file path tokens.
        """
        tokens: list[str] = []
        for path in changed_files:
            parts = re.split(r"[/_\-\.]", path)
            for part in parts:
                if part and part.lower() not in STOPWORDS and len(part) > 2:
                    tokens.append(part.lower())
        return self._deduplicate_tokens(tokens)

    def _tokenize_and_clean(
        self,
        text: str,
        min_length: int = 2,
    ) -> list[str]:
        """Tokenize text into lowercase alphanumeric words, filtering out stopwords.

        Args:
            text: Input raw text string.
            min_length: Minimum word length.

        Returns:
            List of cleaned tokens.
        """
        # Split on non-alphanumeric characters
        raw_words = re.findall(r"[a-zA-Z0-9_]+", text)
        cleaned_tokens: list[str] = []

        for word in raw_words:
            lower_word = word.lower()
            if (
                lower_word not in STOPWORDS
                and len(lower_word) >= min_length
                and not lower_word.isdigit()
            ):
                cleaned_tokens.append(lower_word)

            # Also break down camelCase and snake_case identifiers
            sub_tokens = self._tokenize_identifier(word)
            if len(sub_tokens) > 1:
                for token in sub_tokens:
                    lower = token.lower()
                    if (
                        lower not in STOPWORDS
                        and len(lower) >= min_length
                        and not lower.isdigit()
                    ):
                        cleaned_tokens.append(lower)

        return self._deduplicate_tokens(cleaned_tokens)

    def _tokenize_identifier(self, identifier: str) -> list[str]:
        """Break down camelCase, PascalCase, or snake_case identifiers into individual words.

        Args:
            identifier: Code identifier string.

        Returns:
            List of constituent word tokens.
        """
        # Insert space before capital letters in camelCase
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1 \2", identifier)
        s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s1)
        # Split on spaces, underscores, hyphens
        parts = re.split(r"[_\-\s]+", s2)
        return [p for p in parts if p]

    def _deduplicate_tokens(self, tokens: list[str]) -> list[str]:
        """Deduplicate a list of string tokens while preserving insertion order.

        Args:
            tokens: Sequence of tokens.

        Returns:
            Deduplicated list of tokens.
        """
        seen: set[str] = set()
        deduped: list[str] = []
        for token in tokens:
            key = token.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(token)
        return deduped
