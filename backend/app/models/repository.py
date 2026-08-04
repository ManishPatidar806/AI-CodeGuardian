from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.analytics import ReviewAnalytics
    from app.models.merge_request import MergeRequest


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )

    gitlab_project_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    path_with_namespace: Mapped[str] = mapped_column(
        String(500), nullable=False, unique=True
    )

    default_branch: Mapped[str] = mapped_column(
        String(255), nullable=False, default="main"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    merge_requests: Mapped[list["MergeRequest"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )

    analytics: Mapped["ReviewAnalytics | None"] = relationship(
        back_populates="repository",
        uselist=False,
        cascade="all, delete-orphan",
    )
