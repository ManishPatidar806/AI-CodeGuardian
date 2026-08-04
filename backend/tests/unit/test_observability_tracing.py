from fastapi import FastAPI
from fastapi.testclient import TestClient
import structlog

from app.core.correlation import CORRELATION_ID_HEADER, CorrelationIdMiddleware
from app.core.logging_config import setup_logging
from app.core.sentry import capture_exception, init_sentry
from app.core.telemetry import in_memory_exporter, telemetry_service
from app.core.trace_propagation import extract_trace_context, inject_trace_context


def test_telemetry_span_creation() -> None:
    """Verify TelemetryService creates OpenTelemetry spans in memory."""
    in_memory_exporter.clear()

    with telemetry_service.start_span("test_span_review", attributes={"mr_id": 101}):
        pass

    spans = in_memory_exporter.get_finished_spans()
    assert len(spans) >= 1
    span_names = [s.name for s in spans]
    assert "test_span_review" in span_names


def test_structured_logging() -> None:
    """Verify setup_logging configures structlog without exceptions."""
    setup_logging(log_level="DEBUG", json_format=True)
    logger = structlog.get_logger("test_logger")
    logger.info("structured_log_test_event", metric="cpu_usage", val=42)


def test_sentry_initialization() -> None:
    """Verify Sentry SDK gracefully handles unconfigured DSN."""
    initialized = init_sentry(dsn=None)
    assert initialized is False

    # Should run without raising errors
    capture_exception(ValueError("Test error for Sentry capture"), tags={"component": "unit_test"})


def test_correlation_id_middleware() -> None:
    """Verify CorrelationIdMiddleware generates and propagates X-Correlation-ID headers."""
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/ping")
    def ping():
        return {"status": "ok"}

    client = TestClient(app)

    # 1. Automatic Correlation ID Generation
    res1 = client.get("/ping")
    assert res1.status_code == 200
    assert CORRELATION_ID_HEADER in res1.headers
    assert res1.headers[CORRELATION_ID_HEADER].startswith("corr_")

    # 2. Incoming Correlation ID Propagation
    custom_id = "corr_custom_123456"
    res2 = client.get("/ping", headers={CORRELATION_ID_HEADER: custom_id})
    assert res2.status_code == 200
    assert res2.headers[CORRELATION_ID_HEADER] == custom_id


def test_trace_context_propagation() -> None:
    """Verify inject_trace_context and extract_trace_context for background tasks."""
    structlog.contextvars.bind_contextvars(correlation_id="corr_bg_999")

    headers = inject_trace_context({"existing_header": "value"})
    assert "traceparent" in headers or "X-Correlation-ID" in headers
    assert headers.get("X-Correlation-ID") == "corr_bg_999"

    extract_trace_context(headers)
    ctx_vars = structlog.contextvars.get_contextvars()
    assert ctx_vars.get("correlation_id") == "corr_bg_999"
