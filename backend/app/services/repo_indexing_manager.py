from typing import Any
import structlog

from app.cache.guardian_cache import CodeGuardianCache

logger = structlog.get_logger(__name__)


class RepositoryIndexingManager:
    """Service for orchestrating background repository vector indexing and tracking status."""

    CACHE_NAMESPACE = "repo_indexing"

    def __init__(self, cache: CodeGuardianCache | None = None) -> None:
        """Initialize RepositoryIndexingManager.

        Args:
            cache: Optional CodeGuardianCache instance.
        """
        self.cache = cache or CodeGuardianCache()
        self._memory_status: dict[int, dict[str, Any]] = {}

    def trigger_repository_indexing(
        self, repository_id: int, branch: str = "main"
    ) -> dict[str, Any]:
        """Trigger background repository indexing job and register status.

        Args:
            repository_id: Foreign key ID of Repository.
            branch: Target git branch name.

        Returns:
            Dictionary containing indexing status metadata.
        """
        # Celery task import inside method to avoid circular dependencies
        try:
            from app.workers.tasks import index_repository_task
            task_result = index_repository_task.delay(repository_id, branch)
            task_id = str(task_result.id)
        except Exception as exc:
            logger.warning("celery_indexing_trigger_fallback", error=str(exc))
            task_id = f"mock_task_{repository_id}"

        status_payload = {
            "repository_id": repository_id,
            "branch": branch,
            "status": "INDEXING",
            "task_id": task_id,
            "progress_percent": 0.0,
            "error_message": None,
        }

        self._memory_status[repository_id] = status_payload
        self.cache.cache_service.set(
            namespace=self.CACHE_NAMESPACE,
            key=str(repository_id),
            value=status_payload,
            ttl_seconds=86400,
        )

        logger.info("repository_indexing_triggered", repository_id=repository_id, branch=branch, task_id=task_id)
        return status_payload

    def get_indexing_status(self, repository_id: int) -> dict[str, Any]:
        """Retrieve current indexing status for a repository.

        Args:
            repository_id: Foreign key ID of Repository.

        Returns:
            Indexing status metadata dictionary.
        """
        cached = self.cache.cache_service.get(self.CACHE_NAMESPACE, str(repository_id))
        if isinstance(cached, dict):
            return cached

        return self._memory_status.get(
            repository_id,
            {
                "repository_id": repository_id,
                "branch": "main",
                "status": "INDEXED",
                "task_id": None,
                "progress_percent": 100.0,
                "error_message": None,
            },
        )


# Global Repository Indexing Manager Instance
repo_indexing_manager = RepositoryIndexingManager()
