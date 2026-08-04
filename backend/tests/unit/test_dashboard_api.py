from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.api.v1.dashboard import router as dashboard_router
from app.db.base import Base
from app.db.session import get_db


from sqlalchemy.pool import StaticPool


@pytest.fixture
def client() -> TestClient:
    """Fixture providing TestClient with an in-memory SQLite database session override and seeded test data."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


    session = TestingSession()
    repo = app.models.Repository(
        gitlab_project_id=1,
        name="AI CodeGuardian",
        path_with_namespace="owner/ai-codeguardian",
        default_branch="main"
    )
    session.add(repo)
    session.flush()

    dev = app.models.Developer(
        username="lead_engineer",
        name="Lead Engineer",
        email="lead@company.com"
    )
    session.add(dev)
    session.flush()

    mr = app.models.MergeRequest(
        repository_id=repo.id,
        gitlab_iid=101,
        title="Add Authentication",
        source_branch="feat/auth",
        target_branch="main",
        author_username=dev.username
    )
    session.add(mr)
    session.flush()

    rev = app.models.Review(
        merge_request_id=mr.id,
        commit_sha="abc123sha",
        status="completed",
        score=95.0,
        grade="A+",
        risk_label="LOW",
        summary="Clean security scan.",
        duration_ms=450.0
    )
    session.add(rev)
    session.flush()

    finding = app.models.ReviewFinding(
        review_id=rev.id,
        source="sast",
        category="security",
        severity="medium",
        title="Upgrade Password Hashing",
        description="Use Argon2id",
        suggestion="from passlib.context import CryptContext",
        file_path="app/core/auth.py",
        line_number=45
    )
    session.add(finding)
    session.commit()
    session.close()

    fastapi_app = FastAPI()
    fastapi_app.include_router(dashboard_router)

    def override_get_db():
        db_sess = TestingSession()
        try:
            yield db_sess
        finally:
            db_sess.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    return TestClient(fastapi_app)


def test_get_dashboard_overview(client: TestClient) -> None:
    """Verify GET /dashboard/overview returns complete Web UI dataset."""
    response = client.get("/dashboard/overview")
    assert response.status_code == 200

    data = response.json()
    assert "overview" in data
    assert "reviews" in data
    assert "repositories" in data
    assert "leaderboard" in data
    assert "findings" in data

    assert data["overview"]["total_reviews"] == 1
    assert len(data["reviews"]) == 1
    assert len(data["repositories"]) == 1
    assert len(data["leaderboard"]) == 1
    assert len(data["findings"]) == 1


def test_get_review_detail(client: TestClient) -> None:
    """Verify GET /dashboard/reviews/{id} returns interactive detail view payload."""
    response = client.get("/dashboard/reviews/1")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == 1
    assert "summary" in data
    assert "score" in data
    assert "findings" in data



def test_frontend_assets_integrity() -> None:
    """Verify Web UI React frontend assets exist and are populated."""
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    frontend_dir = root_dir / "frontend"

    html_file = frontend_dir / "index.html"
    app_file = frontend_dir / "src" / "App.jsx"
    css_file = frontend_dir / "src" / "index.css"
    pkg_file = frontend_dir / "package.json"

    assert html_file.exists()
    assert app_file.exists()
    assert css_file.exists()
    assert pkg_file.exists()

    assert "AI CodeGuardian" in html_file.read_text(encoding="utf-8")
    assert "activeTab" in app_file.read_text(encoding="utf-8")
    assert "@tailwind" in css_file.read_text(encoding="utf-8")

