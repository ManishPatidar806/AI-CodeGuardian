from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.merge_request import MergeRequest
from app.repositories.base import BaseRepository


class MergeRequestRepository(BaseRepository[MergeRequest]):
    """Data access repository for MergeRequest entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_id(self, mr_id: int) -> MergeRequest | None:
        """Fetch merge request by primary key ID."""
        return self.db.get(MergeRequest, mr_id)

    def get_by_repo_and_iid(self, repository_id: int, gitlab_iid: int) -> MergeRequest | None:
        """Fetch merge request by repository ID and GitLab IID."""
        stmt = select(MergeRequest).where(
            MergeRequest.repository_id == repository_id,
            MergeRequest.gitlab_iid == gitlab_iid,
        )
        return self.db.scalars(stmt).first()

    def create_or_update(
        self,
        repository_id: int,
        gitlab_iid: int,
        title: str,
        source_branch: str,
        target_branch: str,
        description: str | None = None,
        author_username: str | None = None,
        head_sha: str | None = None,
        web_url: str | None = None,
        state: str = "opened",
    ) -> MergeRequest:
        """Create a new merge request record or update existing matching record."""
        mr = self.get_by_repo_and_iid(repository_id, gitlab_iid)
        if mr:
            mr.title = title
            mr.source_branch = source_branch
            mr.target_branch = target_branch
            mr.description = description
            mr.author_username = author_username
            mr.head_sha = head_sha
            mr.web_url = web_url
            mr.state = state
        else:
            mr = MergeRequest(
                repository_id=repository_id,
                gitlab_iid=gitlab_iid,
                title=title,
                description=description,
                source_branch=source_branch,
                target_branch=target_branch,
                author_username=author_username,
                head_sha=head_sha,
                web_url=web_url,
                state=state,
            )
            self.db.add(mr)

        self.db.commit()
        self.db.refresh(mr)
        return mr

    def list_by_repository(self, repository_id: int) -> Sequence[MergeRequest]:
        """Fetch all merge requests belonging to a repository."""
        stmt = (
            select(MergeRequest)
            .where(MergeRequest.repository_id == repository_id)
            .order_by(MergeRequest.created_at.desc())
        )
        return self.db.scalars(stmt).all()
