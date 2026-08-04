from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.fix_generator import router as fix_generator_router
from app.review_engine.finding import Finding
from app.review_engine.fix_generator import FixGeneratorEngine, fix_generator_engine


def test_successful_fix_generation_loop() -> None:
    """Verify FixGeneratorEngine processes valid patch and produces GitLab suggestion comment."""
    finding = Finding(
        source="ai_reviewer",
        title="Unused Variable Warning",
        description="Variable 'temp' is declared but never used.",
        file_path="app/utils/math.py",
        line_number=10,
        category="clean_code",
        severity="low",
        suggestion="def compute(val: int) -> int:\n    return val * 2",
    )

    original_code = "def compute(val: int) -> int:\n    temp = 100\n    return val * 2"

    result = fix_generator_engine.process_finding_fix_loop(finding, original_code)

    assert result.is_valid is True
    assert result.ruff_passed is True
    assert result.pytest_passed is True
    assert result.mypy_passed is True
    assert result.validation_error is None
    assert "```suggestion" in result.suggested_comment


def test_rejected_unsafe_fix_loop() -> None:
    """Verify FixGeneratorEngine rejects patch failing validation and details why it is unsafe."""
    engine = FixGeneratorEngine()

    finding = Finding(
        source="ai_reviewer",
        title="Flaky Test Assertion",
        description="Failing unit test logic.",
        file_path="app/core/logic.py",
        line_number=15,
        category="testing",
        severity="high",
        suggestion="def test_run(): RAISE_TEST_FAILURE",
    )

    result = engine.process_finding_fix_loop(finding, "def test_run(): pass")

    assert result.is_valid is False
    assert result.pytest_passed is False
    assert "AI Fix Rejected - Unsafe Patch Detected" in result.suggested_comment
    assert "Pytest Tests" in result.suggested_comment


def test_fix_generator_api_endpoint() -> None:
    """Verify FastAPI POST /fixes/validate API endpoint."""
    app = FastAPI()
    app.include_router(fix_generator_router)
    client = TestClient(app)

    payload = {
        "title": "Use Type Annotation",
        "description": "Function return type missing.",
        "file_path": "app/core/helpers.py",
        "line_number": 5,
        "category": "clean_code",
        "severity": "low",
        "suggestion": "def greet(name: str) -> str:\n    return f'Hello {name}'",
        "original_code": "def greet(name):\n    return f'Hello {name}'",
    }

    res = client.post("/fixes/validate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["is_valid"] is True
    assert "```suggestion" in data["suggested_comment"]
