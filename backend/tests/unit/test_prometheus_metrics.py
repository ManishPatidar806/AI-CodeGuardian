from fastapi.testclient import TestClient

from app.api.v1.metrics import router as metrics_router
from app.core.metrics import PrometheusMetricsService, metrics_service


def test_prometheus_metrics_service_singleton() -> None:
    """Verify PrometheusMetricsService maintains a singleton instance."""
    service2 = PrometheusMetricsService()
    assert metrics_service is service2


def test_record_review_processed() -> None:
    """Verify recording of reviews processed metric."""
    metrics_service.record_review_processed("completed")
    metrics_service.record_review_processed("failed")

    content, media_type = metrics_service.generate_metrics_exposition()
    decoded = content.decode("utf-8")
    assert "codeguardian_reviews_processed_total" in decoded
    assert 'status="completed"' in decoded


def test_record_rule_findings() -> None:
    """Verify recording of rule engine findings metric."""
    metrics_service.record_rule_finding(category="security", severity="critical", count=2)

    content, _ = metrics_service.generate_metrics_exposition()
    decoded = content.decode("utf-8")
    assert "codeguardian_rule_engine_findings_total" in decoded
    assert 'category="security"' in decoded
    assert 'severity="critical"' in decoded


def test_record_ai_review_latency() -> None:
    """Verify recording of AI reviewer latency histogram."""
    metrics_service.record_ai_review_latency(reviewer_name="SecurityReviewer", duration_seconds=1.45)

    content, _ = metrics_service.generate_metrics_exposition()
    decoded = content.decode("utf-8")
    assert "codeguardian_ai_review_latency_seconds" in decoded
    assert 'reviewer_name="SecurityReviewer"' in decoded


def test_record_tokens_consumed() -> None:
    """Verify recording of LLM token consumption metrics."""
    metrics_service.record_tokens_consumed(prompt_tokens=500, completion_tokens=150, model_name="gemini-2.5-flash")

    content, _ = metrics_service.generate_metrics_exposition()
    decoded = content.decode("utf-8")
    assert "codeguardian_llm_tokens_consumed_total" in decoded
    assert 'token_type="prompt"' in decoded
    assert 'token_type="completion"' in decoded


def test_record_llm_cost() -> None:
    """Verify recording of LLM estimated cost metrics."""
    metrics_service.record_llm_cost(cost_usd=0.0025, model_name="gemini-2.5-flash")

    content, _ = metrics_service.generate_metrics_exposition()
    decoded = content.decode("utf-8")
    assert "codeguardian_llm_cost_usd_total" in decoded


def test_record_auto_merge_evaluation() -> None:
    """Verify recording of auto-merge evaluation results."""
    metrics_service.record_auto_merge_evaluation(status="merged")
    metrics_service.record_auto_merge_evaluation(status="rejected")

    content, _ = metrics_service.generate_metrics_exposition()
    decoded = content.decode("utf-8")
    assert "codeguardian_auto_merge_evaluations_total" in decoded
    assert 'status="merged"' in decoded


def test_record_failed_review() -> None:
    """Verify recording of failed reviews counter."""
    metrics_service.record_failed_review(error_type="GitLabTimeout")

    content, _ = metrics_service.generate_metrics_exposition()
    decoded = content.decode("utf-8")
    assert "codeguardian_review_failures_total" in decoded
    assert 'error_type="GitLabTimeout"' in decoded


def test_metrics_exposition_endpoint() -> None:
    """Verify FastAPI /metrics endpoint HTTP response."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(metrics_router)
    client = TestClient(app)

    response = client.get("/metrics")
    assert response.status_code == 200
    assert "codeguardian_reviews_processed_total" in response.text
    assert "text/plain" in response.headers["content-type"]
