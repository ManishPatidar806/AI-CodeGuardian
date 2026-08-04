from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.coordinator import CoordinatedReviewResult, ReviewCoordinator
from app.ai.reviewers.architecture import ArchitectureReviewer
from app.ai.reviewers.base import BaseAIReviewer
from app.ai.reviewers.clean_code import CleanCodeReviewer
from app.ai.reviewers.performance import PerformanceReviewer
from app.ai.reviewers.security import SecurityReviewer
from app.ai.reviewers.testing import TestingReviewer
from app.ai.schemas import AIFinding, AIReviewResponse
from app.review_engine.finding import Finding


def create_mock_reviewer(name: str, findings: list[AIFinding] | None = None, raise_error: Exception | None = None) -> BaseAIReviewer:
    """Helper factory to create mock BaseAIReviewer instances for unit tests."""
    mock_reviewer = MagicMock(spec=BaseAIReviewer)
    mock_reviewer.reviewer_name = name

    if raise_error:
        mock_reviewer.areview = AsyncMock(side_effect=raise_error)
    else:
        response = AIReviewResponse(
            summary=f"Summary for {name}",
            findings=findings or [],
        )
        mock_reviewer.areview = AsyncMock(return_value=response)

        # Implementation of to_findings matching BaseAIReviewer behavior
        mock_reviewer.to_findings.side_effect = lambda resp: [
            Finding(
                source=f"ai:{name}",
                category=f.category,
                severity=f.severity,
                title=f.title,
                description=f.description,
                suggestion=f.suggestion,
                file_path=f.file_path,
                line_number=f.line_number,
            )
            for f in resp.findings
        ]

    return mock_reviewer


def test_review_coordinator_default_initialization() -> None:
    """Verify ReviewCoordinator initializes with all 5 default AI reviewers when none provided."""
    coordinator = ReviewCoordinator()
    assert len(coordinator.reviewers) == 5
    types = [type(r) for r in coordinator.reviewers]
    assert SecurityReviewer in types
    assert PerformanceReviewer in types
    assert CleanCodeReviewer in types
    assert TestingReviewer in types
    assert ArchitectureReviewer in types


def test_review_coordinator_custom_dependency_injection() -> None:
    """Verify ReviewCoordinator respects custom injected reviewers."""
    mock_sec = create_mock_reviewer("security")
    mock_perf = create_mock_reviewer("performance")

    coordinator = ReviewCoordinator(reviewers=[mock_sec, mock_perf])
    assert len(coordinator.reviewers) == 2
    assert coordinator.reviewers[0] == mock_sec
    assert coordinator.reviewers[1] == mock_perf


@pytest.mark.asyncio
async def test_review_coordinator_execute_review_success() -> None:
    """Verify concurrent execution of reviewers, finding aggregation, and metric calculation."""
    sec_finding = AIFinding(
        category="security",
        severity="critical",
        title="SQL Injection",
        description="Raw query concatenated with untrusted input",
        file_path="app/db/query.py",
        line_number=42,
    )
    perf_finding = AIFinding(
        category="performance",
        severity="high",
        title="N+1 Query",
        description="Query executed inside loop",
        file_path="app/services/user.py",
        line_number=88,
    )

    mock_sec = create_mock_reviewer("security", findings=[sec_finding])
    mock_perf = create_mock_reviewer("performance", findings=[perf_finding])

    coordinator = ReviewCoordinator(reviewers=[mock_sec, mock_perf])

    diff_content = "+ Select * from users where id = " + "id"
    context_content = "Repository architecture summary..."

    result = await coordinator.execute_review(diff_content, context_content)

    assert isinstance(result, CoordinatedReviewResult)
    assert len(result.findings) == 2
    assert len(result.responses) == 2
    assert len(result.errors) == 0
    assert result.duration_ms >= 0.0

    # Verify findings content
    sec_converted = result.findings[0]
    assert sec_converted.source == "ai:security"
    assert sec_converted.severity == "critical"
    assert sec_converted.title == "SQL Injection"
    assert sec_converted.file_path == "app/db/query.py"
    assert sec_converted.line_number == 42

    perf_converted = result.findings[1]
    assert perf_converted.source == "ai:performance"
    assert perf_converted.severity == "high"
    assert perf_converted.title == "N+1 Query"

    # Verify calls to reviewers
    mock_sec.areview.assert_awaited_once_with(diff_content, context_content)
    mock_perf.areview.assert_awaited_once_with(diff_content, context_content)


@pytest.mark.asyncio
async def test_review_coordinator_fault_tolerance_partial_failure() -> None:
    """Verify that a failure in one reviewer does not crash the coordinator or drop findings from other reviewers."""
    sec_finding = AIFinding(
        category="security",
        severity="high",
        title="Hardcoded Credential",
        description="Found API token in code",
    )
    mock_sec = create_mock_reviewer("security", findings=[sec_finding])
    mock_failing_perf = create_mock_reviewer(
        "performance", raise_error=RuntimeError("LLM rate limit exceeded")
    )

    coordinator = ReviewCoordinator(reviewers=[mock_sec, mock_failing_perf])

    result = await coordinator.execute_review("diff content", "context content")

    assert len(result.findings) == 1
    assert "security" in result.responses
    assert "performance" in result.errors
    assert "LLM rate limit exceeded" in result.errors["performance"]
    assert result.findings[0].title == "Hardcoded Credential"


@pytest.mark.asyncio
async def test_review_coordinator_all_reviewers_failing() -> None:
    """Verify behavior when all reviewers encounter exceptions."""
    mock_r1 = create_mock_reviewer("reviewer_1", raise_error=ValueError("Error 1"))
    mock_r2 = create_mock_reviewer("reviewer_2", raise_error=TimeoutError("Error 2"))

    coordinator = ReviewCoordinator(reviewers=[mock_r1, mock_r2])

    result = await coordinator.execute_review("diff", "context")

    assert len(result.findings) == 0
    assert len(result.responses) == 0
    assert len(result.errors) == 2
    assert "ValueError: Error 1" in result.errors["reviewer_1"]
    assert "TimeoutError: Error 2" in result.errors["reviewer_2"]


def test_review_coordinator_execute_review_sync() -> None:
    """Verify synchronous execution wrapper functionality."""
    mock_sec = create_mock_reviewer("security", findings=[])
    coordinator = ReviewCoordinator(reviewers=[mock_sec])

    result = coordinator.execute_review_sync("diff", "context")

    assert isinstance(result, CoordinatedReviewResult)
    assert "security" in result.responses
    assert len(result.errors) == 0
