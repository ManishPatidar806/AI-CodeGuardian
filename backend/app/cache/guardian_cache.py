from typing import Any
import structlog

from app.cache.redis_service import RedisCacheService

logger = structlog.get_logger(__name__)


class CodeGuardianCache:
    """Specialized domain cache manager for AI CodeGuardian.

    The CodeGuardianCache forms Phase 10 of the backend pipeline.
    It provides dedicated methods to cache and retrieve:
    1. Repository Analysis (AST parsing, dependency graphs)
    2. Embeddings (SentenceTransformer vector representations)
    3. Prompt Context (Budgeted prompt strings)
    4. GitLab API Responses (MR details, diffs, tree metadata)
    5. Project Summaries (Architecture overview documents)
    """

    def __init__(self, cache_service: RedisCacheService | None = None) -> None:
        """Initialize CodeGuardianCache.

        Args:
            cache_service: Optional RedisCacheService instance.
        """
        self.cache_service = cache_service or RedisCacheService()

    # -----------------------------------------------------------------
    # 1. Repository Analysis Cache
    # -----------------------------------------------------------------
    def cache_repository_analysis(
        self,
        project_id: int,
        commit_sha: str,
        analysis_data: dict[str, Any],
        ttl_seconds: int = 86400,  # 24 hours
    ) -> bool:
        """Cache AST parsing and dependency analysis for a repository commit.

        Args:
            project_id: GitLab project ID.
            commit_sha: Commit SHA string.
            analysis_data: Dictionary containing AST/dependency graph metadata.
            ttl_seconds: Cache TTL in seconds.

        Returns:
            True if cached successfully, False otherwise.
        """
        key = f"{project_id}:{commit_sha}"
        logger.debug("caching_repository_analysis", project_id=project_id, commit_sha=commit_sha)
        return self.cache_service.set(
            namespace="repo_analysis",
            key=key,
            value=analysis_data,
            ttl_seconds=ttl_seconds,
        )

    def get_repository_analysis(
        self,
        project_id: int,
        commit_sha: str,
    ) -> dict[str, Any] | None:
        """Fetch cached repository analysis for a commit.

        Args:
            project_id: GitLab project ID.
            commit_sha: Commit SHA string.

        Returns:
            Cached analysis dictionary or None.
        """
        key = f"{project_id}:{commit_sha}"
        return self.cache_service.get(namespace="repo_analysis", key=key)

    # -----------------------------------------------------------------
    # 2. Embeddings Cache
    # -----------------------------------------------------------------
    def cache_embedding(
        self,
        text: str,
        embedding: list[float],
        model_name: str = "sentence-transformers",
        ttl_seconds: int = 604800,  # 7 days
    ) -> bool:
        """Cache vector embedding floats for a text string.

        Args:
            text: Input source code or text snippet.
            embedding: Calculated list of floating point embedding vector numbers.
            model_name: Embedding model identifier.
            ttl_seconds: Cache TTL in seconds.

        Returns:
            True if cached successfully, False otherwise.
        """
        text_hash = self.cache_service.hash_string(text)
        key = f"{model_name}:{text_hash}"
        logger.debug("caching_embedding", model_name=model_name, hash=text_hash)
        return self.cache_service.set(
            namespace="embeddings",
            key=key,
            value=embedding,
            ttl_seconds=ttl_seconds,
        )

    def get_embedding(
        self,
        text: str,
        model_name: str = "sentence-transformers",
    ) -> list[float] | None:
        """Fetch cached vector embedding floats for a text string.

        Args:
            text: Input text string.
            model_name: Embedding model identifier.

        Returns:
            List of floats or None if not cached.
        """
        text_hash = self.cache_service.hash_string(text)
        key = f"{model_name}:{text_hash}"
        result = self.cache_service.get(namespace="embeddings", key=key)
        if isinstance(result, list):
            return [float(x) for x in result]
        return None

    # -----------------------------------------------------------------
    # 3. Prompt Context Cache
    # -----------------------------------------------------------------
    def cache_prompt_context(
        self,
        mr_iid: int,
        commit_sha: str,
        context_text: str,
        ttl_seconds: int = 3600,  # 1 hour
    ) -> bool:
        """Cache assembled prompt context string for an MR commit.

        Args:
            mr_iid: Merge Request IID.
            commit_sha: Commit SHA string.
            context_text: Budgeted context string.
            ttl_seconds: Cache TTL in seconds.

        Returns:
            True if cached, False otherwise.
        """
        key = f"{mr_iid}:{commit_sha}"
        logger.debug("caching_prompt_context", mr_iid=mr_iid, commit_sha=commit_sha)
        return self.cache_service.set(
            namespace="prompt_ctx",
            key=key,
            value={"text": context_text},
            ttl_seconds=ttl_seconds,
        )

    def get_prompt_context(
        self,
        mr_iid: int,
        commit_sha: str,
    ) -> str | None:
        """Fetch cached prompt context string for an MR commit.

        Args:
            mr_iid: Merge Request IID.
            commit_sha: Commit SHA string.

        Returns:
            Cached context string or None.
        """
        key = f"{mr_iid}:{commit_sha}"
        data = self.cache_service.get(namespace="prompt_ctx", key=key)
        if isinstance(data, dict):
            return str(data.get("text", ""))
        return None

    # -----------------------------------------------------------------
    # 4. GitLab API Response Cache
    # -----------------------------------------------------------------
    def cache_gitlab_api_response(
        self,
        endpoint: str,
        params_key: str,
        response_data: Any,
        ttl_seconds: int = 1800,  # 30 minutes
    ) -> bool:
        """Cache raw GitLab API responses.

        Args:
            endpoint: API endpoint path (e.g. '/merge_requests/42/diffs').
            params_key: String representation of query parameters.
            response_data: Deserialized response payload.
            ttl_seconds: Cache TTL in seconds.

        Returns:
            True if cached, False otherwise.
        """
        combined = f"{endpoint}:{params_key}"
        hash_key = self.cache_service.hash_string(combined)
        logger.debug("caching_gitlab_api_response", endpoint=endpoint)
        return self.cache_service.set(
            namespace="gitlab_api",
            key=hash_key,
            value=response_data,
            ttl_seconds=ttl_seconds,
        )

    def get_gitlab_api_response(
        self,
        endpoint: str,
        params_key: str,
    ) -> Any | None:
        """Fetch cached GitLab API response.

        Args:
            endpoint: API endpoint path.
            params_key: String representation of query parameters.

        Returns:
            Cached response payload or None.
        """
        combined = f"{endpoint}:{params_key}"
        hash_key = self.cache_service.hash_string(combined)
        return self.cache_service.get(namespace="gitlab_api", key=hash_key)

    # -----------------------------------------------------------------
    # 5. Project Summaries Cache
    # -----------------------------------------------------------------
    def cache_project_summary(
        self,
        project_id: int,
        commit_sha: str,
        summary_text: str,
        ttl_seconds: int = 86400,  # 24 hours
    ) -> bool:
        """Cache high-level project summary documentation.

        Args:
            project_id: GitLab project ID.
            commit_sha: Commit SHA string.
            summary_text: Project architecture summary text.
            ttl_seconds: Cache TTL in seconds.

        Returns:
            True if cached, False otherwise.
        """
        key = f"{project_id}:{commit_sha}"
        logger.debug("caching_project_summary", project_id=project_id, commit_sha=commit_sha)
        return self.cache_service.set(
            namespace="proj_summary",
            key=key,
            value={"summary": summary_text},
            ttl_seconds=ttl_seconds,
        )

    def get_project_summary(
        self,
        project_id: int,
        commit_sha: str,
    ) -> str | None:
        """Fetch cached project summary.

        Args:
            project_id: GitLab project ID.
            commit_sha: Commit SHA string.

        Returns:
            Summary string or None if missing.
        """
        key = f"{project_id}:{commit_sha}"
        data = self.cache_service.get(namespace="proj_summary", key=key)
        if isinstance(data, dict):
            return str(data.get("summary", ""))
        return None
