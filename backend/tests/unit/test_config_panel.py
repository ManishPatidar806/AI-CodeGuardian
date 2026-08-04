from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from app.api.v1.config import router as config_router
from app.core.config_manager import ConfigurationManager, GuardianConfig, config_manager


def test_guardian_config_defaults() -> None:
    """Verify GuardianConfig default field values."""
    config = GuardianConfig()
    assert config.review_score_threshold == 80.0
    assert config.auto_merge_score_threshold == 85.0
    assert config.llm_model == "gemini-2.5-flash"
    assert config.rules_enabled["security"] is True
    assert config.token_budgets["p1_git_diff_pct"] == 45


def test_guardian_config_budget_validation() -> None:
    """Verify GuardianConfig rejects token budget allocations that do not sum to 100%."""
    with pytest.raises(ValidationError):
        GuardianConfig(
            token_budgets={
                "p1_git_diff_pct": 50,
                "p2_rag_pct": 50,
                "p3_dep_graph_pct": 50,
                "p4_summary_pct": 50,  # Total = 200%, should raise ValidationError
            }
        )


def test_config_manager_get_and_update() -> None:
    """Verify ConfigurationManager updates state dynamically."""
    config_manager.update_config(GuardianConfig())
    manager = ConfigurationManager()
    initial = manager.get_config()
    assert initial.review_score_threshold == 80.0

    new_cfg = GuardianConfig(
        review_score_threshold=85.0,
        auto_merge_score_threshold=90.0,
        llm_model="gemini-2.5-pro",
    )
    updated = manager.update_config(new_cfg)
    assert updated.review_score_threshold == 85.0
    assert updated.llm_model == "gemini-2.5-pro"


def test_config_api_endpoints() -> None:
    """Verify FastAPI GET and PUT /config API endpoints."""
    config_manager.update_config(GuardianConfig())
    app = FastAPI()
    app.include_router(config_router)
    client = TestClient(app)

    # 1. GET /config
    get_res = client.get("/config")
    assert get_res.status_code == 200
    cfg_data = get_res.json()
    assert cfg_data["review_score_threshold"] == 80.0

    # 2. PUT /config
    update_payload = {
        "review_score_threshold": 88.0,
        "auto_merge_score_threshold": 92.0,
        "llm_model": "gemini-2.5-pro",
        "rules_enabled": {
            "security": True,
            "performance": True,
            "clean_code": True,
            "testing": False,
            "architecture": True,
        },
        "token_budgets": {
            "p1_git_diff_pct": 40,
            "p2_rag_pct": 30,
            "p3_dep_graph_pct": 20,
            "p4_summary_pct": 10,
        },
        "slack_channel": "#dev-alerts",
        "slack_notification_trigger": "on_critical_only",
    }

    put_res = client.put("/config", json=update_payload)
    assert put_res.status_code == 200
    updated_data = put_res.json()
    assert updated_data["review_score_threshold"] == 88.0
    assert updated_data["rules_enabled"]["testing"] is False
    assert updated_data["slack_channel"] == "#dev-alerts"
