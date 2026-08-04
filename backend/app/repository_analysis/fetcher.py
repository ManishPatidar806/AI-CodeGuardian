from dataclasses import dataclass

import structlog

from app.integrations.gitlab.client import GitLabClient
from app.repository_analysis.file_filter import (
    RepositoryFileFilter,
)


logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class RepositoryFile:
    path: str
    content: str


class RepositoryFetcher:
    def __init__(
        self,
        gitlab_client: GitLabClient,
    ) -> None:
        self.gitlab_client = gitlab_client
        self.file_filter = RepositoryFileFilter()

    def fetch(
        self,
        project_id: int,
        ref: str,
    ) -> list[RepositoryFile]:
        tree = self.gitlab_client.get_repository_tree(
            project_id=project_id,
            ref=ref,
        )

        files: list[RepositoryFile] = []

        for item in tree:
            if item.get("type") != "blob":
                continue

            file_path = item.get("path")

            if not file_path:
                continue

            if not self.file_filter.should_analyze(file_path):
                continue

            try:
                content = self.gitlab_client.get_file_content(
                    project_id=project_id,
                    file_path=file_path,
                    ref=ref,
                )

            except Exception:
                logger.exception(
                    "repository_file_fetch_failed",
                    project_id=project_id,
                    file_path=file_path,
                )
                continue

            files.append(
                RepositoryFile(
                    path=file_path,
                    content=content,
                )
            )

        logger.info(
            "repository_fetch_completed",
            project_id=project_id,
            ref=ref,
            files=len(files),
        )

        return files
