from fastapi.testclient import TestClient

from app.api.v1.grafana import router as grafana_router
from app.services.grafana_service import GrafanaDashboardService


def test_grafana_dashboard_json_file_exists() -> None:
    """Verify Grafana dashboard JSON file exists and loads."""
    service = GrafanaDashboardService()
    data = service.load_dashboard_json()
    assert data["title"] == "AI CodeGuardian Overview"
    assert data["schemaVersion"] == 36
    assert data["uid"] == "ai_codeguardian_overview"


def test_grafana_dashboard_schema_validation() -> None:
    """Verify dashboard JSON schema passes validation checks."""
    service = GrafanaDashboardService()
    assert service.validate_dashboard_schema() is True


def test_grafana_panel_definitions() -> None:
    """Verify all 7 requested Grafana dashboard panels exist."""
    service = GrafanaDashboardService()
    panels = service.get_panel_definitions()
    assert len(panels) == 7

    titles = [p["title"] for p in panels]
    assert "Review Throughput (per min)" in titles
    assert "Score Distribution & Auto-Merge Status" in titles
    assert "AI Latency p95 (seconds)" in titles
    assert "Token Consumption Rate (tokens/sec)" in titles
    assert "Cost Accumulation ($ USD)" in titles
    assert "Top Security Findings by Category & Severity" in titles
    assert "Rule Engine vs AI Engine Distribution" in titles


def test_promql_query_alignment() -> None:
    """Verify PromQL expressions reference Phase 12 Prometheus metrics."""
    service = GrafanaDashboardService()
    panels = service.get_panel_definitions()

    all_exprs: list[str] = []
    for p in panels:
        targets = p.get("targets", [])
        for t in targets:
            expr = t.get("expr", "")
            if expr:
                all_exprs.append(expr)

    combined_promql = " ".join(all_exprs)
    assert "codeguardian_reviews_processed_total" in combined_promql
    assert "codeguardian_ai_review_latency_seconds_bucket" in combined_promql
    assert "codeguardian_llm_tokens_consumed_total" in combined_promql
    assert "codeguardian_llm_cost_usd_total" in combined_promql
    assert "codeguardian_rule_engine_findings_total" in combined_promql
    assert "codeguardian_auto_merge_evaluations_total" in combined_promql


def test_grafana_api_endpoint() -> None:
    """Verify FastAPI GET /grafana/dashboard provisioning endpoint."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(grafana_router)
    client = TestClient(app)

    response = client.get("/grafana/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "AI CodeGuardian Overview"
    assert len(data["panels"]) == 7
