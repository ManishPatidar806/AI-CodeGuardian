import asyncio
import time
from dataclasses import dataclass, field
from typing import Sequence

import structlog

from app.ai.reviewers.architecture import ArchitectureReviewer
from app.ai.reviewers.base import BaseAIReviewer
from app.ai.reviewers.clean_code import CleanCodeReviewer
from app.ai.reviewers.performance import PerformanceReviewer
from app.ai.reviewers.security import SecurityReviewer
from app.ai.reviewers.testing import TestingReviewer
from app.ai.schemas import AIReviewResponse
from app.review_engine.finding import Finding

logger = structlog.get_logger(__name__)


@dataclass
class CoordinatedReviewResult:
    """Unified response object returned by ReviewCoordinator.

    Contains all converted domain findings, individual AI review responses,
    captured reviewer errors, and execution metrics.
    """

    findings: list[Finding] = field(default_factory=list)
    responses: dict[str, AIReviewResponse] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    duration_ms: float = 0.0


class ReviewCoordinator:
    """Orchestrates concurrent execution of independent AI reviewers.

    The ReviewCoordinator acts as an orchestrator layer in the AI review pipeline.
    It executes all registered AI reviewers concurrently (e.g. security, performance,
    clean code, testing, architecture), collects their structured AIReviewResponse objects,
    converts responses into domain Finding entities, and aggregates execution metrics
    and error states in a fault-tolerant manner.
    """

    def __init__(
        self,
        reviewers: Sequence[BaseAIReviewer] | None = None,
    ) -> None:
        """Initialize ReviewCoordinator with a list of AI reviewers.

        Args:
            reviewers: Optional sequence of BaseAIReviewer instances. If None,
                defaults to instantiating the full suite of specialized AI reviewers:
                [SecurityReviewer, PerformanceReviewer, CleanCodeReviewer, TestingReviewer, ArchitectureReviewer].
        """
        if reviewers is not None:
            self.reviewers: list[BaseAIReviewer] = list(reviewers)
        else:
            self.reviewers = [
                SecurityReviewer(),
                PerformanceReviewer(),
                CleanCodeReviewer(),
                TestingReviewer(),
                ArchitectureReviewer(),
            ]

    async def execute_review(
        self,
        diff: str,
        repository_context: str,
    ) -> CoordinatedReviewResult:
        """Concurrently execute all configured AI reviewers against the provided code diff and context.

        Args:
            diff: The unified git diff string of changes to review.
            repository_context: Assembled RAG repository context (code chunks, summary, dependency graph).

        Returns:
            CoordinatedReviewResult containing unified domain findings, individual AI responses,
            reviewer errors (if any), and total wall-clock duration in milliseconds.
        """
        start_time = time.perf_counter()

        logger.info(
            "review_coordination_started",
            reviewer_count=len(self.reviewers),
            reviewer_names=[r.reviewer_name for r in self.reviewers],
            diff_length=len(diff),
            context_length=len(repository_context),
        )

        # Create concurrent review tasks for each reviewer
        tasks = [
            self._execute_single_reviewer(reviewer, diff, repository_context)
            for reviewer in self.reviewers
        ]

        # Execute all reviewer tasks concurrently using gather with return_exceptions=True
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_findings: list[Finding] = []
        responses: dict[str, AIReviewResponse] = {}
        errors: dict[str, str] = {}

        for reviewer, result in zip(self.reviewers, results):
            name = reviewer.reviewer_name

            if isinstance(result, Exception):
                error_msg = f"{type(result).__name__}: {str(result)}"
                logger.error(
                    "reviewer_execution_failed",
                    reviewer=name,
                    error=error_msg,
                    exc_info=result,
                )
                errors[name] = error_msg
            elif isinstance(result, tuple) and len(result) == 2:
                response, reviewer_findings = result
                responses[name] = response
                all_findings.extend(reviewer_findings)
                logger.info(
                    "reviewer_execution_succeeded",
                    reviewer=name,
                    findings_count=len(reviewer_findings),
                )
            else:
                error_msg = f"Unexpected reviewer return type: {type(result)}"
                logger.error(
                    "reviewer_execution_unexpected_return",
                    reviewer=name,
                    error=error_msg,
                )
                errors[name] = error_msg

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        logger.info(
            "review_coordination_completed",
            total_findings=len(all_findings),
            successful_reviewers=len(responses),
            failed_reviewers=len(errors),
            duration_ms=round(elapsed_ms, 2),
        )

        return CoordinatedReviewResult(
            findings=all_findings,
            responses=responses,
            errors=errors,
            duration_ms=round(elapsed_ms, 2),
        )

    async def _execute_single_reviewer(
        self,
        reviewer: BaseAIReviewer,
        diff: str,
        repository_context: str,
    ) -> tuple[AIReviewResponse, list[Finding]]:
        """Internal helper to execute a single reviewer and convert its response to domain findings.

        Args:
            reviewer: The BaseAIReviewer instance to execute.
            diff: Git diff text.
            repository_context: Relevant repository context text.

        Returns:
            Tuple of (AIReviewResponse, list[Finding]).

        Raises:
            Exception: Propagates any exception encountered during LLM execution or conversion.
        """
        logger.debug("reviewer_execution_started", reviewer=reviewer.reviewer_name)

        response = await reviewer.areview(diff, repository_context)
        findings = reviewer.to_findings(response)

        return response, findings

    def execute_review_sync(
        self,
        diff: str,
        repository_context: str,
    ) -> CoordinatedReviewResult:
        """Synchronous wrapper for execute_review for use in synchronous execution contexts (e.g. Celery workers).

        Args:
            diff: Unified git diff string.
            repository_context: Assembled RAG repository context.

        Returns:
            CoordinatedReviewResult containing findings, responses, errors, and metrics.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If already running in an event loop (e.g. inside an async web server), create a new thread or use run_until_complete
            import nest_asyncio  # type: ignore

            nest_asyncio.apply()
            return loop.run_until_complete(self.execute_review(diff, repository_context))

        return asyncio.run(self.execute_review(diff, repository_context))
