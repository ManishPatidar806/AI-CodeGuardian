from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.review import Review


class PromptHistory(Base):
    """SQLAlchemy model for auditing LLM prompts and responses per review."""

    __tablename__ = "prompt_histories"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    review_id: Mapped[int] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_template_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    review: Mapped["Review"] = relationship(back_populates="prompt_histories")
