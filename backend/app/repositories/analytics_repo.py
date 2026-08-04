from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analytics import ReviewAnalytics
from app.models.review import Review
from app.models.review_finding import ReviewFinding
from app.repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository[ReviewAnalytics]):
    """Data access repository for computing and persisting repository review analytics."""

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_repository_id(self, repository_id: int) -> ReviewAnalytics | None:
        """Fetch review analytics for a repository."""
        stmt = select(ReviewAnalytics).where(ReviewAnalytics.repository_id == repository_id)
        return self.db.scalars(stmt).first()

    def update_repository_analytics(
        self,
        repository_id: int,
        latest_review_score: float,
        findings_count: int,
        critical_count: int = 0,
        high_count: int = 0,
    ) -> ReviewAnalytics:
        """Update or initialize aggregated metrics for a repository upon review completion.

        Args:
            repository_id: Foreign key ID of Repository.
            latest_review_score: Numerical score of latest review.
            findings_count: Count of findings in latest review.
            critical_count: Count of critical findings.
            high_count: Count of high findings.

        Returns:
            Updated ReviewAnalytics instance.
        """
        analytics = self.get_by_repository_id(repository_id)

        if not analytics:
            analytics = ReviewAnalytics(
                repository_id=repository_id,
                total_reviews=1,
                average_score=round(latest_review_score, 2),
                total_findings=findings_count,
                critical_findings_count=critical_count,
                high_findings_count=high_count,
            )
            self.db.add(analytics)
        else:
            # Compute running average score
            prev_total = analytics.total_reviews
            new_total = prev_total + 1
            new_avg = ((analytics.average_score * prev_total) + latest_review_score) / new_total

            analytics.total_reviews = new_total
            analytics.average_score = round(new_avg, 2)
            analytics.total_findings += findings_count
            analytics.critical_findings_count += critical_count
            analytics.high_findings_count += high_count

        self.db.commit()
        self.db.refresh(analytics)
        return analytics

    def get_global_analytics_summary(self) -> dict[str, float | int]:
        """Compute system-wide aggregated review statistics."""
        total_reviews = self.db.scalar(select(func.count(Review.id))) or 0
        avg_score = self.db.scalar(select(func.avg(Review.score))) or 0.0
        total_findings = self.db.scalar(select(func.count(ReviewFinding.id))) or 0
        total_critical = (
            self.db.scalar(
                select(func.count(ReviewFinding.id)).where(ReviewFinding.severity == "critical")
            )
            or 0
        )

        return {
            "total_reviews": int(total_reviews),
            "average_score": round(float(avg_score), 2),
            "total_findings": int(total_findings),
            "critical_findings": int(total_critical),
        }
