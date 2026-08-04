from unittest.mock import MagicMock
import pytest
from app.cache.guardian_cache import CodeGuardianCache
from app.cache.redis_service import RedisCacheService


def create_mock_redis_client() -> MagicMock:
    """Helper factory for a mock redis.Redis instance."""
    mock_redis = MagicMock()
    storage: dict[str, str] = {}

    def mock_get(key: str) -> str | None:
        return storage.get(key)

    def mock_set(key: str, val: str, ex: int | None = None) -> bool:
        storage[key] = val
        return True

    def mock_setex(key: str, ttl: int, val: str) -> bool:
        storage[key] = val
        return True

    def mock_delete(*keys: str) -> int:
        count = 0
        for k in keys:
            if k in storage:
                del storage[k]
                count += 1
        return count

    def mock_exists(key: str) -> int:
        return 1 if key in storage else 0

    mock_redis.get.side_effect = mock_get
    mock_redis.set.side_effect = mock_set
    mock_redis.setex.side_effect = mock_setex
    mock_redis.delete.side_effect = mock_delete
    mock_redis.exists.side_effect = mock_exists
    return mock_redis


def test_redis_service_set_get_delete() -> None:
    """Verify RedisCacheService basic get, set, delete, and exists operations."""
    service = RedisCacheService()
    service._client = create_mock_redis_client()

    # 1. Set & Get
    success = service.set(namespace="test_ns", key="item1", value={"foo": "bar"})
    assert success is True

    val = service.get(namespace="test_ns", key="item1")
    assert val == {"foo": "bar"}

    # 2. Exists
    assert service.exists(namespace="test_ns", key="item1") is True

    # 3. Delete
    deleted = service.delete(namespace="test_ns", key="item1")
    assert deleted is True
    assert service.get(namespace="test_ns", key="item1") is None


def test_graceful_fallback_when_redis_unavailable() -> None:
    """Verify RedisCacheService handles missing/failed Redis connection gracefully."""
    service = RedisCacheService()
    service._client = None  # Simulate offline/disconnected Redis

    assert service.get("ns", "key") is None
    assert service.set("ns", "key", "val") is False
    assert service.delete("ns", "key") is False
    assert service.exists("ns", "key") is False
    assert service.delete_by_pattern("*") == 0


def test_cache_repository_analysis() -> None:
    """Verify CodeGuardianCache repository analysis caching."""
    service = RedisCacheService()
    service._client = create_mock_redis_client()
    cache = CodeGuardianCache(cache_service=service)

    analysis_data = {
        "ast_nodes": 150,
        "imports": ["os", "sys", "fastapi"],
        "classes": ["User", "Repository"],
    }

    cached = cache.cache_repository_analysis(
        project_id=42, commit_sha="sha123", analysis_data=analysis_data
    )
    assert cached is True

    result = cache.get_repository_analysis(project_id=42, commit_sha="sha123")
    assert result is not None
    assert result["ast_nodes"] == 150
    assert "fastapi" in result["imports"]


def test_cache_embeddings() -> None:
    """Verify CodeGuardianCache text embedding vector caching."""
    service = RedisCacheService()
    service._client = create_mock_redis_client()
    cache = CodeGuardianCache(cache_service=service)

    vector = [0.123, 0.456, -0.789, 0.001]
    text = "def authenticate_user(username, password): pass"

    cached = cache.cache_embedding(text=text, embedding=vector)
    assert cached is True

    retrieved = cache.get_embedding(text=text)
    assert retrieved is not None
    assert len(retrieved) == 4
    assert retrieved[0] == pytest.approx(0.123)
    assert retrieved[2] == pytest.approx(-0.789)


def test_cache_prompt_context() -> None:
    """Verify CodeGuardianCache prompt context string caching."""
    service = RedisCacheService()
    service._client = create_mock_redis_client()
    cache = CodeGuardianCache(cache_service=service)

    prompt_ctx = "=== CHANGED GIT DIFF (P1) ===\n+ def test(): pass"
    cached = cache.cache_prompt_context(mr_iid=5, commit_sha="sha_abc", context_text=prompt_ctx)
    assert cached is True

    result = cache.get_prompt_context(mr_iid=5, commit_sha="sha_abc")
    assert result == prompt_ctx


def test_cache_gitlab_api_response() -> None:
    """Verify CodeGuardianCache raw GitLab API response caching."""
    service = RedisCacheService()
    service._client = create_mock_redis_client()
    cache = CodeGuardianCache(cache_service=service)

    api_payload = [{"id": 1, "title": "MR 1"}, {"id": 2, "title": "MR 2"}]
    cached = cache.cache_gitlab_api_response(
        endpoint="/projects/10/merge_requests",
        params_key="state=opened&per_page=100",
        response_data=api_payload,
    )
    assert cached is True

    result = cache.get_gitlab_api_response(
        endpoint="/projects/10/merge_requests",
        params_key="state=opened&per_page=100",
    )
    assert result is not None
    assert len(result) == 2
    assert result[0]["title"] == "MR 1"


def test_cache_project_summary() -> None:
    """Verify CodeGuardianCache project summary documentation caching."""
    service = RedisCacheService()
    service._client = create_mock_redis_client()
    cache = CodeGuardianCache(cache_service=service)

    summary = "=== PROJECT ARCHITECTURE SUMMARY ===\nFastAPI backend with Redis and PostgreSQL."
    cached = cache.cache_project_summary(project_id=99, commit_sha="sha_xyz", summary_text=summary)
    assert cached is True

    result = cache.get_project_summary(project_id=99, commit_sha="sha_xyz")
    assert result == summary
