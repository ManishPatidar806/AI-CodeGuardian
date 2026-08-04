from datetime import datetime, timezone
import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.gitlab.client import GitLabClient
from app.models.merge_request import MergeRequest
from app.models.repository import Repository
from app.models.review import Review
from app.models.review_finding import ReviewFinding
from app.review_engine.context import ReviewContext
from app.review_engine.engine import ReviewEngine
from app.review_engine.rules import get_default_rules
from app.review_engine.scoring import ScoreCalculator
from app.review_engine.finding import Finding

logger = structlog.get_logger(__name__)


class ReviewOrchestrator:
    def __init__(
        self,
        db: Session,
        gitlab_client: GitLabClient,
    ) -> None:
        self.db = db
        self.gitlab_client = gitlab_client

        self.engine = ReviewEngine(
            rules=get_default_rules(),
        )

        self.score_calculator = ScoreCalculator()

    def _get_merge_request(
        self,
        merge_request_id: int,
    ) -> MergeRequest:
        statement = select(MergeRequest).where(MergeRequest.id == merge_request_id)
        merge_request = self.db.scalar(statement)
        if merge_request is None:
            raise ValueError(f"Merge request {merge_request_id} not found")
        return merge_request

    def _get_repository(
        self,
        repository_id: int,
    ) -> Repository:
        statement = select(Repository).where(Repository.id == repository_id)
        repository = self.db.scalar(statement)
        if repository is None:
            raise ValueError(f"Repository {repository_id} not found")
        return repository

    def _build_context(
        self,
        repository: Repository,
        merge_request: MergeRequest,
    ) -> ReviewContext:
        project_id = repository.gitlab_project_id
        mr_iid = merge_request.gitlab_iid

        mr = self.gitlab_client.get_merge_request(
            project_id,
            mr_iid,
        )

        commits = self.gitlab_client.get_merge_request_commits(
            project_id,
            mr_iid,
        )

        diffs = self.gitlab_client.get_merge_request_diffs(
            project_id,
            mr_iid,
        )

        return ReviewContext(
            project_id=project_id,
            mr_iid=mr_iid,
            title=mr["title"],
            description=mr.get("description"),
            source_branch=mr["source_branch"],
            target_branch=mr["target_branch"],
            commits=commits,
            diffs=diffs,
        )

    def _create_review(
        self,
        merge_request: MergeRequest,
    ) -> Review:
        if not merge_request.head_sha:
            raise ValueError("Merge request does not have a head SHA")

        review = Review(
            merge_request_id=merge_request.id,
            commit_sha=merge_request.head_sha,
            status="running",
            started_at=datetime.now(timezone.utc),
        )

        self.db.add(review)
        self.db.flush()

        return review

    def _save_findings(
        self,
        review: Review,
        findings: list[Finding],
    ) -> None:
        for finding in findings:
            db_finding = ReviewFinding(
                review_id=review.id,
                source=finding.source,
                category=finding.category,
                severity=finding.severity,
                file_path=finding.file_path,
                line_number=finding.line_number,
                title=finding.title,
                description=finding.description,
                suggestion=finding.suggestion,
            )

            self.db.add(db_finding)

    def run_review(
        self,
        merge_request_id: int,
    ) -> Review:
        merge_request = self._get_merge_request(merge_request_id)

        repository = self._get_repository(merge_request.repository_id)

        review = self._create_review(merge_request)

        try:
            context = self._build_context(
                repository,
                merge_request,
            )

            findings = self.engine.run(context)

            score = self.score_calculator.calculate(findings)

            self._save_findings(
                review,
                findings,
            )

            review.score = score
            review.status = "completed"
            review.completed_at = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(review)

            logger.info(
                "review_completed",
                review_id=review.id,
                merge_request_id=merge_request.id,
                score=score,
                findings=len(findings),
            )

            return review

        except Exception:
            self.db.rollback()

            logger.exception(
                "review_failed",
                merge_request_id=merge_request.id,
            )

            raise
