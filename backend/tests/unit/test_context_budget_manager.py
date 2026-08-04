from app.repository_analysis.models import CodeChunk
from app.retrieval.hybrid_retriever import (
    RepositoryContext,
    RetrievalResult,
    StructuralContext,
)
from app.ai.context_budget_manager import (
    BudgetContextResult,
    ContextBudget,
    ContextBudgetManager,
    TokenCounter,
)


def test_token_counter_estimation_and_truncation() -> None:
    """Verify TokenCounter accurately counts tokens and cleanly truncates text at line boundaries."""
    counter = TokenCounter()

    sample_text = "Line 1: Hello World\nLine 2: Python Code Guardian\nLine 3: RAG Retrieval"
    tokens = counter.count_tokens(sample_text)
    assert tokens > 0

    # Truncate to a tight token budget
    truncated, was_trunc = counter.truncate_to_tokens(sample_text, max_tokens=10)
    assert was_trunc is True
    assert "TRUNCATED" in truncated
    assert counter.count_tokens(truncated) <= 20


def test_budget_prioritization_and_allocation() -> None:
    """Verify ContextBudgetManager prioritizes Git Diff (P1) > Semantic (P2) > Dependency (P3) > Summary (P4)."""
    manager = ContextBudgetManager()

    diff_content = "def test_func():\n    return 42\n"
    sem_result = RetrievalResult(
        content="class User:\n    pass",
        file_path="app/models/user.py",
        language="python",
        score=0.9,
    )
    summary_content = "AI CodeGuardian architecture summary overview."

    result = manager.build_budgeted_context(
        diff=diff_content,
        semantic_results=[sem_result],
        project_summary=summary_content,
    )

    assert isinstance(result, BudgetContextResult)
    assert "=== CHANGED GIT DIFF (P1) ===" in result.formatted_context
    assert "=== SEMANTICALLY RELATED CODE (P2) ===" in result.formatted_context
    assert "=== PROJECT ARCHITECTURE SUMMARY (P4) ===" in result.formatted_context
    assert result.diff_tokens > 0
    assert result.semantic_tokens > 0
    assert result.summary_tokens > 0
    assert result.total_tokens > 0
    assert result.budget_utilization_pct > 0.0


def test_cascading_unused_budget_transfer() -> None:
    """Verify unused tokens from a small git diff cascade down to lower-priority tiers."""
    budget = ContextBudget(max_total_tokens=4000, prompt_overhead_tokens=1000)
    manager = ContextBudgetManager(budget=budget)

    # Net context budget = 3000 tokens
    # P1 Diff quota = 1350 tokens. Small diff uses ~10 tokens -> ~1340 tokens cascade to P2/P3/P4!
    small_diff = "+ x = 1"

    # Large semantic content that requires cascading tokens (base P2 quota is 750 tokens)
    large_semantic = [
        RetrievalResult(
            content="def large_block_"
            + str(i)
            + "():\n    "
            + ("# extensive documentation line and logic block\n" * 30),
            file_path=f"app/services/service_{i}.py",
            language="python",
            score=0.95,
        )
        for i in range(8)
    ]

    result = manager.build_budgeted_context(
        diff=small_diff,
        semantic_results=large_semantic,
    )

    assert result.diff_tokens < 50
    # Semantic tier received cascaded budget from P1
    assert result.semantic_tokens > 500
    assert "git_diff" not in result.truncated_sections


def test_truncation_when_exceeding_budget() -> None:
    """Verify large diff exceeding quota gets truncated cleanly at line boundaries."""
    # Set a small token budget to force truncation
    budget = ContextBudget(max_total_tokens=1500, prompt_overhead_tokens=1000)
    manager = ContextBudgetManager(budget=budget)

    # Huge diff (500 lines) exceeding P1 quota (225 tokens)
    huge_diff = "\n".join([f"+ line {i}: print('spam eggs')" for i in range(500)])

    result = manager.build_budgeted_context(diff=huge_diff)

    assert "git_diff" in result.truncated_sections
    assert "... [TRUNCATED DUE TO CONTEXT BUDGET]" in result.formatted_context


def test_hard_custom_token_limit_enforcement() -> None:
    """Verify custom_max_tokens strictly limits total assembled context size."""
    manager = ContextBudgetManager()

    diff_content = "\n".join([f"+ line {i}" for i in range(100)])
    summary_content = "Summary text " * 100

    result = manager.build_budgeted_context(
        diff=diff_content,
        project_summary=summary_content,
        custom_max_tokens=1500,  # 1500 total - 1000 overhead = 500 net budget
    )

    # Total tokens should not exceed net budget plus small formatting header
    assert result.total_tokens <= 600


def test_empty_and_none_inputs() -> None:
    """Verify graceful handling when all input components are empty or None."""
    manager = ContextBudgetManager()
    result = manager.build_budgeted_context(
        diff="",
        semantic_results=[],
        structural_results=[],
        project_summary=None,
    )

    assert result.formatted_context == ""
    assert result.total_tokens == 0
    assert result.diff_tokens == 0
    assert len(result.truncated_sections) == 0


def test_repository_context_integration() -> None:
    """Verify building budgeted context using RepositoryContext object."""
    manager = ContextBudgetManager()

    rep_context = RepositoryContext(
        semantic_results=[
            RetrievalResult(
                content="def sem(): pass",
                file_path="sem.py",
                language="python",
                score=0.9,
            )
        ],
        structural_results=[
            StructuralContext(
                file_path="struct.py",
                relationship="dependency",
                chunks=[
                    CodeChunk(
                        file_path="struct.py",
                        language="python",
                        content="def struct(): pass",
                        start_line=1,
                        end_line=2,
                    )
                ],
            )
        ],
    )

    result = manager.build_budgeted_context(
        diff="+ new code",
        repository_context=rep_context,
    )

    assert "=== CHANGED GIT DIFF (P1) ===" in result.formatted_context
    assert "=== SEMANTICALLY RELATED CODE (P2) ===" in result.formatted_context
    assert "=== DEPENDENCY & STRUCTURAL CONTEXT (P3) ===" in result.formatted_context
