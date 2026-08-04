import hashlib
import json
from typing import Any
import redis
import structlog

from app.core.settings import settings

logger = structlog.get_logger(__name__)


class RedisCacheService:
    """Low-level Redis client service handling JSON serialization, TTL expiry, and pattern operations."""

    def __init__(
        self,
        redis_url: str | None = None,
        prefix: str = "cg",
    ) -> None:
        """Initialize RedisCacheService.

        Args:
            redis_url: Optional Redis connection URL (defaults to settings.redis_url).
            prefix: Global key namespace prefix.
        """
        self.url = redis_url or getattr(settings, "redis_url", "redis://localhost:6379")
        self.prefix = prefix.strip(":")
        self._client: redis.Redis | None = None

        try:
            self._client = redis.Redis.from_url(
                self.url,
                decode_responses=True,
                socket_timeout=3.0,
                socket_connect_timeout=3.0,
            )
        except Exception as exc:
            logger.warning("redis_connection_failed_at_init", error=str(exc), url=self.url)
            self._client = None

    def _make_key(self, namespace: str, key: str) -> str:
        """Construct a namespaced Redis key (e.g. 'cg:namespace:key')."""
        clean_ns = namespace.strip(":")
        clean_key = key.strip(":")
        return f"{self.prefix}:{clean_ns}:{clean_key}"

    def get(self, namespace: str, key: str) -> Any | None:
        """Retrieve and deserialize a JSON object from Redis.

        Args:
            namespace: Sub-namespace (e.g. 'embeddings', 'repo_analysis').
            key: Target cache key.

        Returns:
            Deserialized Python object or None if missing/failed.
        """
        if not self._client:
            return None

        full_key = self._make_key(namespace, key)
        try:
            raw = self._client.get(full_key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning("redis_get_failed", key=full_key, error=str(exc))
            return None

    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: int | None = 86400,
    ) -> bool:
        """Serialize and store an object in Redis with an optional TTL.

        Args:
            namespace: Sub-namespace.
            key: Target cache key.
            value: Python object to serialize to JSON.
            ttl_seconds: Time-to-live in seconds (defaults to 86400 / 24 hours).

        Returns:
            True if successfully cached, False otherwise.
        """
        if not self._client:
            return False

        full_key = self._make_key(namespace, key)
        try:
            serialized = json.dumps(value, default=str)
            if ttl_seconds and ttl_seconds > 0:
                self._client.set(full_key, serialized, ex=ttl_seconds)
            else:
                self._client.set(full_key, serialized)
            return True
        except Exception as exc:
            logger.warning("redis_set_failed", key=full_key, error=str(exc))
            return False

    def delete(self, namespace: str, key: str) -> bool:
        """Delete a single key from Redis.

        Args:
            namespace: Sub-namespace.
            key: Target cache key.

        Returns:
            True if deleted, False otherwise.
        """
        if not self._client:
            return False

        full_key = self._make_key(namespace, key)
        try:
            res = self._client.delete(full_key)
            return bool(res)
        except Exception as exc:
            logger.warning("redis_delete_failed", key=full_key, error=str(exc))
            return False

    def delete_by_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Args:
            pattern: Glob-style pattern (e.g. 'repo_analysis:*').

        Returns:
            Count of deleted keys.
        """
        if not self._client:
            return 0

        full_pattern = f"{self.prefix}:{pattern.lstrip(':')}"
        try:
            keys = list(self._client.scan_iter(match=full_pattern, count=100))
            if keys:
                return int(self._client.delete(*keys))
            return 0
        except Exception as exc:
            logger.warning("redis_delete_by_pattern_failed", pattern=full_pattern, error=str(exc))
            return 0

    def exists(self, namespace: str, key: str) -> bool:
        """Check if a key exists in Redis."""
        if not self._client:
            return False
        full_key = self._make_key(namespace, key)
        try:
            return bool(self._client.exists(full_key))
        except Exception as exc:
            logger.warning("redis_exists_failed", key=full_key, error=str(exc))
            return False

    @staticmethod
    def hash_string(text: str) -> str:
        """Utility helper to generate deterministic MD5 hash for long texts or params."""
        return hashlib.md5(text.encode("utf-8")).hexdigest()
