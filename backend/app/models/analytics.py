from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.repository import Repository


class ReviewAnalytics(Base):
    """SQLAlchemy model for aggregated repository review metrics."""

    __tablename__ = "review_analytics"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_findings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    critical_findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    repository: Mapped["Repository"] = relationship(back_populates="analytics")
