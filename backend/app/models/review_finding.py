from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
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
    from app.models.review import Review


class ReviewFinding(Base):
    __tablename__ = "review_findings"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    review_id: Mapped[int] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    file_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    line_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    suggestion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    review: Mapped["Review"] = relationship(
        back_populates="findings",
    )
