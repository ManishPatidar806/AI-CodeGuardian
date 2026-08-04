from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.developer import Developer
from app.repositories.base import BaseRepository


class DeveloperRepository(BaseRepository[Developer]):
    """Data access repository for Developer entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_id(self, developer_id: int) -> Developer | None:
        """Fetch developer by primary key ID."""
        return self.db.get(Developer, developer_id)

    def get_by_username(self, username: str) -> Developer | None:
        """Fetch developer by username."""
        stmt = select(Developer).where(Developer.username == username.strip())
        return self.db.scalars(stmt).first()

    def create_or_update(
        self,
        username: str,
        email: str | None = None,
        name: str | None = None,
        gitlab_user_id: int | None = None,
    ) -> Developer:
        """Create a new developer record or update an existing record."""
        clean_user = username.strip()
        dev = self.get_by_username(clean_user)
        if dev:
            if email:
                dev.email = email
            if name:
                dev.name = name
            if gitlab_user_id:
                dev.gitlab_user_id = gitlab_user_id
        else:
            dev = Developer(
                username=clean_user,
                email=email,
                name=name,
                gitlab_user_id=gitlab_user_id,
            )
            self.db.add(dev)

        self.db.commit()
        self.db.refresh(dev)
        return dev

    def list_all(self) -> Sequence[Developer]:
        """Fetch all registered developers."""
        stmt = select(Developer).order_by(Developer.username)
        return self.db.scalars(stmt).all()
