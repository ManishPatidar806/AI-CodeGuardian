from typing import Any
import structlog
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = structlog.get_logger(__name__)

propagator = TraceContextTextMapPropagator()


def inject_trace_context(headers: dict[str, Any] | None = None) -> dict[str, Any]:
    """Inject current OpenTelemetry trace context and correlation ID into Celery task headers.

    Args:
        headers: Optional existing header dictionary.

    Returns:
        Updated header dictionary containing traceparent and correlation ID.
    """
    header_dict = headers if headers is not None else {}
    propagator.inject(header_dict)

    # Inject correlation_id from structlog contextvars if present
    context_vars = structlog.contextvars.get_contextvars()
    if "correlation_id" in context_vars:
        header_dict["X-Correlation-ID"] = context_vars["correlation_id"]

    return header_dict


def extract_trace_context(headers: dict[str, Any]) -> None:
    """Extract trace context and correlation ID from Celery task headers and bind to current context.

    Args:
        headers: Celery task header dictionary containing traceparent.
    """
    if not headers:
        return

    context = propagator.extract(headers)
    token = trace.use_span(trace.get_current_span(context))  # noqa: F841

    correlation_id = headers.get("X-Correlation-ID") or headers.get("x-correlation-id")
    if correlation_id:
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    logger.debug("trace_context_extracted_for_task", correlation_id=correlation_id)
