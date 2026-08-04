from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.repository import Repository
    from app.models.review import Review


class MergeRequest(Base):
    __tablename__ = "merge_requests"

    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "gitlab_iid",
            name="uq_merge_request_repository_iid",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gitlab_iid: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    target_branch: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    author_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    head_sha: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    state: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="opened",
    )

    web_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    repository: Mapped["Repository"] = relationship(
        back_populates="merge_requests",
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="merge_request",
        cascade="all, delete-orphan",
    )
