from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.repositories.base import BaseRepository


class RepositoryRepository(BaseRepository[Repository]):
    """Data access repository for Repository entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_id(self, repo_id: int) -> Repository | None:
        """Fetch repository by primary key ID."""
        return self.db.get(Repository, repo_id)

    def get_by_gitlab_project_id(self, gitlab_project_id: int) -> Repository | None:
        """Fetch repository by GitLab project ID."""
        stmt = select(Repository).where(Repository.gitlab_project_id == gitlab_project_id)
        return self.db.scalars(stmt).first()

    def get_by_path(self, path_with_namespace: str) -> Repository | None:
        """Fetch repository by namespace path (e.g. 'owner/repo')."""
        stmt = select(Repository).where(Repository.path_with_namespace == path_with_namespace)
        return self.db.scalars(stmt).first()

    def create_or_update(
        self,
        gitlab_project_id: int,
        name: str,
        path_with_namespace: str,
        default_branch: str = "main",
    ) -> Repository:
        """Create a new repository or update existing matching repository."""
        repo = self.get_by_gitlab_project_id(gitlab_project_id)
        if repo:
            repo.name = name
            repo.path_with_namespace = path_with_namespace
            repo.default_branch = default_branch
        else:
            repo = Repository(
                gitlab_project_id=gitlab_project_id,
                name=name,
                path_with_namespace=path_with_namespace,
                default_branch=default_branch,
            )
            self.db.add(repo)

        self.db.commit()
        self.db.refresh(repo)
        return repo

    def list_all(self) -> Sequence[Repository]:
        """Fetch all registered repositories."""
        stmt = select(Repository).order_by(Repository.name)
        return self.db.scalars(stmt).all()
