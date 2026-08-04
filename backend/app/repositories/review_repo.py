from datetime import datetime
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.llm_usage import LLMUsage
from app.models.prompt_history import PromptHistory
from app.models.review import Review
from app.models.review_finding import ReviewFinding
from app.repositories.base import BaseRepository
from app.review_engine.finding import Finding


class ReviewRepository(BaseRepository[Review]):
    """Data access repository for Review history, Findings, Prompt History, and LLM Usage."""

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def create_review_with_findings(
        self,
        merge_request_id: int,
        commit_sha: str,
        score: float | None = None,
        grade: str | None = None,
        risk_label: str | None = None,
        summary: str | None = None,
        model_name: str | None = None,
        duration_ms: float | None = None,
        findings: Sequence[Finding] | None = None,
        status: str = "completed",
    ) -> Review:
        """Create a Review record along with associated ReviewFinding entities in a single atomic transaction.

        Args:
            merge_request_id: Foreign key ID of MergeRequest.
            commit_sha: Commit SHA string.
            score: Quality score (0.0 to 100.0).
            grade: Letter grade ('A+', 'A', 'B', 'C', 'F').
            risk_label: Qualitative risk description.
            summary: Markdown review summary string.
            model_name: Name of AI model used (e.g. 'gemini-2.5-flash').
            duration_ms: Review duration in milliseconds.
            findings: Sequence of domain Finding objects to persist.
            status: Status string ('pending', 'completed', 'failed').

        Returns:
            Persisted Review instance with loaded findings.
        """
        now = datetime.now()
        review = Review(
            merge_request_id=merge_request_id,
            commit_sha=commit_sha,
            score=score,
            grade=grade,
            risk_label=risk_label,
            summary=summary,
            model_name=model_name,
            duration_ms=duration_ms,
            status=status,
            started_at=now,
            completed_at=now,
        )
        self.db.add(review)
        self.db.flush()  # Flush to generate review.id

        # Persist associated findings
        if findings:
            for f in findings:
                db_finding = ReviewFinding(
                    review_id=review.id,
                    source=f.source,
                    category=f.category,
                    severity=f.severity,
                    file_path=f.file_path,
                    line_number=f.line_number,
                    title=f.title,
                    description=f.description,
                    suggestion=f.suggestion,
                )
                self.db.add(db_finding)

        self.db.commit()
        self.db.refresh(review)
        return review

    def record_prompt_history(
        self,
        review_id: int,
        reviewer_name: str,
        prompt_text: str,
        response_text: str | None = None,
        prompt_template_version: str | None = "v1.0",
        tokens_used: int | None = None,
        duration_ms: float | None = None,
    ) -> PromptHistory:
        """Persist LLM prompt and response audit record.

        Args:
            review_id: Associated Review ID.
            reviewer_name: Name of the reviewer module.
            prompt_text: Input prompt text sent to LLM.
            response_text: Raw output response from LLM.
            prompt_template_version: Prompt template version identifier.
            tokens_used: Estimated tokens used by this prompt call.
            duration_ms: Wall-clock latency in milliseconds.

        Returns:
            Persisted PromptHistory object.
        """
        prompt_record = PromptHistory(
            review_id=review_id,
            reviewer_name=reviewer_name,
            prompt_template_version=prompt_template_version,
            prompt_text=prompt_text,
            response_text=response_text,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
        )
        self.db.add(prompt_record)
        self.db.commit()
        self.db.refresh(prompt_record)
        return prompt_record

    def record_llm_usage(
        self,
        review_id: int,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        cost_usd: float | None = None,
    ) -> LLMUsage:
        """Persist LLM token usage, latency, and cost metric.

        Args:
            review_id: Associated Review ID.
            model_name: AI model name (e.g. 'gemini-2.5-flash').
            prompt_tokens: Number of prompt input tokens.
            completion_tokens: Number of completion output tokens.
            latency_ms: Latency in milliseconds.
            cost_usd: Estimated cost in USD.

        Returns:
            Persisted LLMUsage object.
        """
        total_tokens = prompt_tokens + completion_tokens
        usage = LLMUsage(
            review_id=review_id,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
        )
        self.db.add(usage)
        self.db.commit()
        self.db.refresh(usage)
        return usage

    def get_by_id(self, review_id: int) -> Review | None:
        """Fetch review by ID with eager loading of findings, prompt histories, and LLM usages."""
        stmt = (
            select(Review)
            .options(
                joinedload(Review.findings),
                joinedload(Review.prompt_histories),
                joinedload(Review.llm_usages),
            )
            .where(Review.id == review_id)
        )
        return self.db.scalars(stmt).unique().first()

    def list_by_merge_request(self, merge_request_id: int) -> Sequence[Review]:
        """Fetch all historical reviews for a Merge Request ordered by date."""
        stmt = (
            select(Review)
            .options(joinedload(Review.findings))
            .where(Review.merge_request_id == merge_request_id)
            .order_by(Review.created_at.desc())
        )
        return self.db.scalars(stmt).unique().all()
