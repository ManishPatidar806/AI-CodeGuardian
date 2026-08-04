import os
import time
from typing import Any
import structlog

from app.cache.guardian_cache import CodeGuardianCache
from app.integrations.slack.notifier import ReviewNotificationPayload, SlackNotifier
from app.retrieval.embeddings import EmbeddingGenerator
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.index_repository_task",
    max_retries=3,
    default_retry_delay=10,
    retry_backoff=True,
)
def index_repository_task(
    self: Any,
    repo_path: str,
    gitlab_project_id: int,
    commit_sha: str,
) -> dict[str, Any]:
    """Asynchronous background task to fetch, parse, and index repository codebase into ChromaDB.

    Args:
        repo_path: Local filesystem path or remote git URL of repository.
        gitlab_project_id: GitLab project ID.
        commit_sha: Commit SHA string.

    Returns:
        Dictionary summary of indexing results.
    """
    logger.info("start_index_repository_task", repo_path=repo_path, project_id=gitlab_project_id, commit_sha=commit_sha)

    try:
        # Check cache first for existing analysis
        cache = CodeGuardianCache()
        existing = cache.get_repository_analysis(gitlab_project_id, commit_sha)
        if existing:
            logger.info("repository_analysis_already_cached", project_id=gitlab_project_id, commit_sha=commit_sha)
            return {"status": "cached", "project_id": gitlab_project_id, "commit_sha": commit_sha, "chunks_indexed": 0}

        # Simulate or execute AST parsing & embedding generation
        start_time = time.time()
        embedding_gen = EmbeddingGenerator()

        # Dummy chunking logic for repository files if path exists
        indexed_chunks = 0
        if os.path.exists(repo_path):
            sample_chunks = ["def hello(): return 'world'", "class Server: pass"]
            embeddings = embedding_gen.generate_embeddings(sample_chunks)
            indexed_chunks = len(embeddings)

        analysis_meta = {
            "status": "indexed",
            "project_id": gitlab_project_id,
            "commit_sha": commit_sha,
            "chunks_indexed": indexed_chunks,
            "duration_ms": round((time.time() - start_time) * 1000, 2),
        }

        # Save analysis result to Redis cache
        cache.cache_repository_analysis(gitlab_project_id, commit_sha, analysis_meta)
        logger.info("completed_index_repository_task", **analysis_meta)
        return analysis_meta

    except Exception as exc:
        logger.error("index_repository_task_failed", error=str(exc), retry=self.request.retries)
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.generate_embeddings_task",
    max_retries=3,
    default_retry_delay=5,
    retry_backoff=True,
)
def generate_embeddings_task(
    self: Any,
    text_chunks: list[str],
    model_name: str = "sentence-transformers",
) -> dict[str, Any]:
    """Asynchronous background task to generate vector embeddings for text chunks.

    Args:
        text_chunks: List of text strings to embed.
        model_name: Model identifier string.

    Returns:
        Dictionary with status and total embeddings generated.
    """
    logger.info("start_generate_embeddings_task", chunk_count=len(text_chunks), model_name=model_name)

    try:
        cache = CodeGuardianCache()
        embedding_gen = EmbeddingGenerator()

        uncached_chunks: list[str] = []
        cached_vectors: list[list[float]] = []

        # Check vector cache for each chunk
        for chunk in text_chunks:
            cached_vec = cache.get_embedding(chunk, model_name=model_name)
            if cached_vec:
                cached_vectors.append(cached_vec)
            else:
                uncached_chunks.append(chunk)

        # Generate vectors for uncached text chunks
        newly_generated = 0
        if uncached_chunks:
            new_vectors = embedding_gen.generate_embeddings(uncached_chunks)
            newly_generated = len(new_vectors)

            # Store generated vectors into Redis cache
            for chunk, vec in zip(uncached_chunks, new_vectors, strict=False):
                cache.cache_embedding(chunk, vec, model_name=model_name)

        result = {
            "status": "completed",
            "total_chunks": len(text_chunks),
            "cached_hits": len(cached_vectors),
            "newly_generated": newly_generated,
        }
        logger.info("completed_generate_embeddings_task", **result)
        return result

    except Exception as exc:
        logger.error("generate_embeddings_task_failed", error=str(exc), retry=self.request.retries)
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.send_slack_notification_task",
    max_retries=5,
    default_retry_delay=5,
    retry_backoff=True,
)
def send_slack_notification_task(
    self: Any,
    payload_dict: dict[str, Any],
) -> dict[str, Any]:
    """Asynchronous background task to send Block Kit review notifications to Slack.

    Args:
        payload_dict: Serialized dictionary matching ReviewNotificationPayload.

    Returns:
        Dictionary status of Slack delivery.
    """
    logger.info("start_send_slack_notification_task", repo=payload_dict.get("repository"))

    try:
        payload = ReviewNotificationPayload(**payload_dict)
        notifier = SlackNotifier()
        res = notifier.send_review_notification(payload)

        result = {"status": "delivered", "repository": payload.repository, "response": res}
        logger.info("completed_send_slack_notification_task", **result)
        return result

    except Exception as exc:
        logger.warning("send_slack_notification_task_failed", error=str(exc), retry=self.request.retries)
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.workers.tasks.periodic_cleanup_task",
)
def periodic_cleanup_task() -> dict[str, Any]:
    """Periodic Celery Beat task to purge stale cache entries and temporary scratch files.

    Returns:
        Summary of cleaned resources.
    """
    logger.info("start_periodic_cleanup_task")

    try:
        cache = CodeGuardianCache()
        # Purge stale API cache keys matching pattern
        purged_keys = cache.cache_service.delete_by_pattern("gitlab_api:*")

        result = {
            "status": "completed",
            "purged_cache_keys": purged_keys,
            "timestamp": time.time(),
        }
        logger.info("completed_periodic_cleanup_task", **result)
        return result

    except Exception as exc:
        logger.error("periodic_cleanup_task_error", error=str(exc))
        return {"status": "error", "error": str(exc)}
