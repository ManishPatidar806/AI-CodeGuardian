from typing import Generic, TypeVar
from sqlalchemy.orm import Session

from app.db.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic base repository for PostgreSQL data access operations."""

    def __init__(self, db: Session) -> None:
        """Initialize BaseRepository with a SQLAlchemy session.

        Args:
            db: Active SQLAlchemy Session instance.
        """
        self.db = db
