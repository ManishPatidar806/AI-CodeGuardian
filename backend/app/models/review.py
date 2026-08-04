from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.llm_usage import LLMUsage
    from app.models.merge_request import MergeRequest
    from app.models.prompt_history import PromptHistory
    from app.models.review_finding import ReviewFinding


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    merge_request_id: Mapped[int] = mapped_column(
        ForeignKey("merge_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    commit_sha: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    grade: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    risk_label: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    duration_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    merge_request: Mapped["MergeRequest"] = relationship(
        back_populates="reviews",
    )

    findings: Mapped[list["ReviewFinding"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )

    prompt_histories: Mapped[list["PromptHistory"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )

    llm_usages: Mapped[list["LLMUsage"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )
