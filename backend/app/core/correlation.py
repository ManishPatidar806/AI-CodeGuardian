from collections.abc import Awaitable, Callable
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from opentelemetry import trace

logger = structlog.get_logger(__name__)

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """ASGI Middleware to extract, bind, and propagate X-Correlation-ID headers."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Extract correlation ID from request headers or generate new UUID4, bind to structlog contextvars.

        Args:
            request: Incoming FastAPI Request.
            call_next: Next request handler in ASGI chain.

        Returns:
            HTTP Response containing X-Correlation-ID header.
        """
        correlation_id = request.headers.get(
            CORRELATION_ID_HEADER
        ) or request.headers.get("X-Request-ID") or f"corr_{uuid.uuid4().hex[:12]}"

        # Clear and bind contextvars for structlog logging
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # Set correlation ID on active OpenTelemetry span
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.set_attribute("correlation_id", correlation_id)

        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
