from dataclasses import dataclass
import time
import structlog

from app.cache.guardian_cache import CodeGuardianCache

logger = structlog.get_logger(__name__)


@dataclass
class RateLimitResult:
    """Dataclass representing the result of a rate limit evaluation.

    Attributes:
        is_allowed: True if request is within allowed rate limits, else False.
        remaining: Remaining requests allowed in the current time window.
        retry_after_seconds: Seconds to wait before retrying if rate limit was exceeded.
    """

    is_allowed: bool
    remaining: int
    retry_after_seconds: int = 0


class RepoRateLimiter:
    """Sliding-window rate limiter enforcing per-repository request volume limits."""

    CACHE_NAMESPACE = "rate_limit"

    def __init__(self, cache: CodeGuardianCache | None = None) -> None:
        """Initialize RepoRateLimiter.

        Args:
            cache: Optional CodeGuardianCache instance.
        """
        self.cache = cache or CodeGuardianCache()
        self._memory_buckets: dict[int, list[float]] = {}

    def check_rate_limit(
        self,
        repository_id: int,
        max_requests: int = 30,
        window_seconds: int = 60,
    ) -> RateLimitResult:
        """Evaluate sliding-window rate limit for a repository.

        Args:
            repository_id: Foreign key ID of Repository.
            max_requests: Maximum allowed review requests within window.
            window_seconds: Time window duration in seconds.

        Returns:
            RateLimitResult object.
        """
        now = time.time()
        window_start = now - window_seconds

        # Memory bucket fallback / sync
        timestamps = self._memory_buckets.get(repository_id, [])
        # Prune expired timestamps
        valid_timestamps = [ts for ts in timestamps if ts >= window_start]

        if len(valid_timestamps) >= max_requests:
            oldest = valid_timestamps[0]
            retry_after = int(max(1, (oldest + window_seconds) - now))
            logger.warning(
                "repo_rate_limit_exceeded",
                repository_id=repository_id,
                current_count=len(valid_timestamps),
                max_requests=max_requests,
            )
            return RateLimitResult(
                is_allowed=False,
                remaining=0,
                retry_after_seconds=retry_after,
            )

        valid_timestamps.append(now)
        self._memory_buckets[repository_id] = valid_timestamps
        remaining = max(0, max_requests - len(valid_timestamps))

        return RateLimitResult(
            is_allowed=True,
            remaining=remaining,
            retry_after_seconds=0,
        )


# Global Repo Rate Limiter Instance
repo_rate_limiter = RepoRateLimiter()
