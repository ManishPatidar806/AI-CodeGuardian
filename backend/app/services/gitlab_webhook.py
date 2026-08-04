import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.merge_request import MergeRequest
from app.models.repository import Repository
from app.schemas.gitlab import GitLabMergeRequestEvent


logger = structlog.get_logger(__name__)


class GitLabWebhookService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_create_repository(
        self,
        event: GitLabMergeRequestEvent,
    ) -> Repository:
        project = event.project

        statement = select(Repository).where(Repository.gitlab_project_id == project.id)

        repository = self.db.scalar(statement)

        if repository is not None:
            repository.name = project.name
            repository.path_with_namespace = project.path_with_namespace
            repository.default_branch = project.default_branch

            return repository

        repository = Repository(
            gitlab_project_id=project.id,
            name=project.name,
            path_with_namespace=project.path_with_namespace,
            default_branch=project.default_branch,
        )

        self.db.add(repository)
        self.db.flush()

        return repository

    def _upsert_merge_request(
        self,
        repository: Repository,
        event: GitLabMergeRequestEvent,
    ) -> MergeRequest:
        attributes = event.object_attributes

        statement = select(MergeRequest).where(
            MergeRequest.repository_id == repository.id,
            MergeRequest.gitlab_iid == attributes.iid,
        )

        merge_request = self.db.scalar(statement)

        head_sha = (
            attributes.last_commit.id if attributes.last_commit is not None else None
        )

        if merge_request is None:
            merge_request = MergeRequest(
                repository_id=repository.id,
                gitlab_iid=attributes.iid,
                title=attributes.title,
                description=attributes.description,
                source_branch=attributes.source_branch,
                target_branch=attributes.target_branch,
                author_username=event.user.username,
                head_sha=head_sha,
                state=attributes.state,
                web_url=attributes.url,
            )

            self.db.add(merge_request)

            return merge_request

        merge_request.title = attributes.title
        merge_request.description = attributes.description
        merge_request.source_branch = attributes.source_branch
        merge_request.target_branch = attributes.target_branch
        merge_request.author_username = event.user.username
        merge_request.head_sha = head_sha
        merge_request.state = attributes.state
        merge_request.web_url = attributes.url

        return merge_request

    def process_merge_request(
        self,
        event: GitLabMergeRequestEvent,
    ) -> MergeRequest:
        try:
            repository = self._get_or_create_repository(event)

            merge_request = self._upsert_merge_request(
                repository,
                event,
            )

            self.db.commit()
            self.db.refresh(merge_request)

            logger.info(
                "gitlab_merge_request_processed",
                repository_id=repository.id,
                merge_request_id=merge_request.id,
                gitlab_iid=merge_request.gitlab_iid,
                state=merge_request.state,
            )

            return merge_request

        except Exception:
            self.db.rollback()

            logger.exception("gitlab_merge_request_processing_failed")

            raise


class GitLabWebhookResponse(BaseModel):
    status: str
    message: str
    merge_request_id: int | None = None
