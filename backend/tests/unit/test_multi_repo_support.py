from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.repositories.repository_repo import RepositoryRepository  # noqa: F401
import app.models  # noqa: F401
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.repositories import router as repositories_router
from app.core.config_manager import GuardianConfig, config_manager
from app.core.repo_config_manager import RepoConfigOverride, repo_config_manager
from app.db.session import get_db
from app.services.repo_indexing_manager import repo_indexing_manager


from sqlalchemy.pool import StaticPool


@pytest.fixture
def client() -> TestClient:
    """Fixture providing TestClient with an in-memory SQLite database session override."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    app = FastAPI()
    app.include_router(repositories_router)
    app.include_router(dashboard_router)

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_repo_config_override_inheritance() -> None:
    """Verify RepoConfigurationManager merges global config with per-repository overrides."""
    config_manager.update_config(GuardianConfig(review_score_threshold=80.0, llm_model="gemini-2.5-flash"))

    repo_id = 99
    override = RepoConfigOverride(
        repository_id=repo_id,
        review_score_threshold=90.0,
        rules_enabled={"security": True, "testing": False},
    )
    repo_config_manager.set_repo_override(repo_id, override)

    effective = repo_config_manager.get_effective_config(repo_id)
    assert effective.review_score_threshold == 90.0
    assert effective.llm_model == "gemini-2.5-flash"  # Inherited from global
    assert effective.rules_enabled["testing"] is False


def test_repository_indexing_manager() -> None:
    """Verify RepositoryIndexingManager triggers task and returns indexing status."""
    repo_id = 42
    status = repo_indexing_manager.trigger_repository_indexing(repo_id, branch="main")
    assert status["repository_id"] == repo_id
    assert status["status"] == "INDEXING"

    current_status = repo_indexing_manager.get_indexing_status(repo_id)
    assert current_status["status"] == "INDEXING"


def test_repositories_api_endpoints(client: TestClient) -> None:
    """Verify FastAPI /repositories CRUD & config/indexing endpoints."""
    # 1. Register repository
    create_res = client.post(
        "/repositories",
        json={
            "name": "Payment Gateway Service",
            "path_with_namespace": "org/payment-gateway",
            "default_branch": "main",
            "gitlab_project_id": 501,
        },
    )
    assert create_res.status_code == 200
    repo_data = create_res.json()
    repo_id = repo_data["id"]
    assert repo_data["name"] == "Payment Gateway Service"

    # 2. List repositories
    list_res = client.get("/repositories")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Get repository detail
    get_res = client.get(f"/repositories/{repo_id}")
    assert get_res.status_code == 200
    assert get_res.json()["path_with_namespace"] == "org/payment-gateway"

    # 4. Update per-repo config override
    put_config_res = client.put(
        f"/repositories/{repo_id}/config",
        json={
            "repository_id": repo_id,
            "review_score_threshold": 95.0,
            "llm_model": "gpt-4o",
        },
    )
    assert put_config_res.status_code == 200
    assert put_config_res.json()["effective_config"]["review_score_threshold"] == 95.0

    # 5. Trigger indexing
    index_res = client.post(f"/repositories/{repo_id}/index", json={"branch": "main"})
    assert index_res.status_code == 200
    assert index_res.json()["status"] == "INDEXING"


def test_dashboard_repo_filtered(client: TestClient) -> None:
    """Verify GET /dashboard/overview supports repository_id query parameter."""
    res = client.get("/dashboard/overview?repository_id=1")
    assert res.status_code == 200
    data = res.json()
    assert "overview" in data
    assert "reviews" in data
