import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.developer_repo import DeveloperRepository
from app.repositories.merge_request_repo import MergeRequestRepository
from app.repositories.repository_repo import RepositoryRepository
from app.repositories.review_repo import ReviewRepository
from app.review_engine.finding import Finding


@pytest.fixture
def db_session() -> Session:
    """Fixture providing an in-memory SQLite database session for unit testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_repository_crud(db_session: Session) -> None:
    """Verify RepositoryRepository CRUD operations."""
    repo_repository = RepositoryRepository(db_session)

    # 1. Create Repository
    repo = repo_repository.create_or_update(
        gitlab_project_id=101,
        name="AI CodeGuardian",
        path_with_namespace="owner/ai-codeguardian",
        default_branch="main",
    )
    assert repo.id is not None
    assert repo.name == "AI CodeGuardian"

    # 2. Fetch by GitLab Project ID & Path
    fetched_by_id = repo_repository.get_by_gitlab_project_id(101)
    assert fetched_by_id is not None
    assert fetched_by_id.id == repo.id

    fetched_by_path = repo_repository.get_by_path("owner/ai-codeguardian")
    assert fetched_by_path is not None
    assert fetched_by_path.gitlab_project_id == 101

    # 3. Update Repository
    updated = repo_repository.create_or_update(
        gitlab_project_id=101,
        name="AI CodeGuardian Enterprise",
        path_with_namespace="owner/ai-codeguardian-enterprise",
    )
    assert updated.name == "AI CodeGuardian Enterprise"


def test_developer_crud(db_session: Session) -> None:
    """Verify DeveloperRepository CRUD operations."""
    dev_repository = DeveloperRepository(db_session)

    dev = dev_repository.create_or_update(
        username="lead_engineer",
        email="lead@example.com",
        name="Senior Engineer",
        gitlab_user_id=505,
    )

    assert dev.id is not None
    assert dev.username == "lead_engineer"

    fetched = dev_repository.get_by_username("lead_engineer")
    assert fetched is not None
    assert fetched.email == "lead@example.com"


def test_merge_request_crud(db_session: Session) -> None:
    """Verify MergeRequestRepository CRUD operations."""
    repo_repo = RepositoryRepository(db_session)
    mr_repo = MergeRequestRepository(db_session)

    repo = repo_repo.create_or_update(102, "RepoB", "owner/repob")

    mr = mr_repo.create_or_update(
        repository_id=repo.id,
        gitlab_iid=42,
        title="Add JWT Auth",
        description="Implements OAuth2 JWT verification",
        source_branch="feature/jwt",
        target_branch="main",
        author_username="lead_engineer",
    )

    assert mr.id is not None
    assert mr.gitlab_iid == 42

    fetched = mr_repo.get_by_repo_and_iid(repo.id, 42)
    assert fetched is not None
    assert fetched.title == "Add JWT Auth"


def test_review_with_findings_persistence(db_session: Session) -> None:
    """Verify atomic persistence of Review and associated ReviewFinding objects."""
    repo_repo = RepositoryRepository(db_session)
    mr_repo = MergeRequestRepository(db_session)
    review_repo = ReviewRepository(db_session)

    repo = repo_repo.create_or_update(103, "RepoC", "owner/repoc")
    mr = mr_repo.create_or_update(repo.id, 1, "Feature X", "f/x", "main")

    findings = [
        Finding(
            source="ai:security",
            category="security",
            severity="critical",
            title="SQL Injection",
            description="Raw string query",
            file_path="db.py",
            line_number=10,
        ),
        Finding(
            source="rule_engine",
            category="testing",
            severity="medium",
            title="Missing Test",
            description="No unit test",
            file_path="test_db.py",
            line_number=1,
        ),
    ]

    review = review_repo.create_review_with_findings(
        merge_request_id=mr.id,
        commit_sha="sha_abc123",
        score=60.0,
        grade="C",
        risk_label="Serious Issue",
        summary="Review completed with critical finding.",
        model_name="gemini-2.5-flash",
        duration_ms=450.0,
        findings=findings,
    )

    assert review.id is not None
    assert review.score == 60.0
    assert review.grade == "C"

    # Fetch loaded review
    fetched_review = review_repo.get_by_id(review.id)
    assert fetched_review is not None
    assert len(fetched_review.findings) == 2
    assert fetched_review.findings[0].severity == "critical"
    assert fetched_review.findings[1].severity == "medium"


def test_prompt_history_auditing(db_session: Session) -> None:
    """Verify PromptHistory auditing records are persisted."""
    repo_repo = RepositoryRepository(db_session)
    mr_repo = MergeRequestRepository(db_session)
    review_repo = ReviewRepository(db_session)

    repo = repo_repo.create_or_update(104, "RepoD", "owner/repod")
    mr = mr_repo.create_or_update(repo.id, 2, "Fix Y", "f/y", "main")
    review = review_repo.create_review_with_findings(mr.id, "sha1")

    prompt = review_repo.record_prompt_history(
        review_id=review.id,
        reviewer_name="SecurityReviewer",
        prompt_text="Analyze code for vulnerabilities...",
        response_text="Found 0 vulnerabilities.",
        prompt_template_version="v2.1",
        tokens_used=450,
        duration_ms=120.0,
    )

    assert prompt.id is not None
    assert prompt.reviewer_name == "SecurityReviewer"
    assert prompt.tokens_used == 450


def test_llm_usage_tracking(db_session: Session) -> None:
    """Verify LLMUsage token tracking records are persisted."""
    repo_repo = RepositoryRepository(db_session)
    mr_repo = MergeRequestRepository(db_session)
    review_repo = ReviewRepository(db_session)

    repo = repo_repo.create_or_update(105, "RepoE", "owner/repoe")
    mr = mr_repo.create_or_update(repo.id, 3, "Fix Z", "f/z", "main")
    review = review_repo.create_review_with_findings(mr.id, "sha2")

    usage = review_repo.record_llm_usage(
        review_id=review.id,
        model_name="gemini-2.5-flash",
        prompt_tokens=1000,
        completion_tokens=250,
        latency_ms=850.0,
        cost_usd=0.0015,
    )

    assert usage.id is not None
    assert usage.total_tokens == 1250
    assert usage.cost_usd == 0.0015


def test_review_analytics_calculation(db_session: Session) -> None:
    """Verify AnalyticsRepository calculates running averages and finding aggregations."""
    repo_repo = RepositoryRepository(db_session)
    analytics_repo = AnalyticsRepository(db_session)

    repo = repo_repo.create_or_update(106, "RepoF", "owner/repof")

    # First review: score 80.0, 2 findings (1 critical)
    a1 = analytics_repo.update_repository_analytics(
        repository_id=repo.id,
        latest_review_score=80.0,
        findings_count=2,
        critical_count=1,
        high_count=0,
    )

    assert a1.total_reviews == 1
    assert a1.average_score == 80.0
    assert a1.total_findings == 2

    # Second review: score 100.0, 0 findings
    a2 = analytics_repo.update_repository_analytics(
        repository_id=repo.id,
        latest_review_score=100.0,
        findings_count=0,
        critical_count=0,
        high_count=0,
    )

    assert a2.total_reviews == 2
    assert a2.average_score == 90.0  # (80 + 100) / 2
    assert a2.total_findings == 2
