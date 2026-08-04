from collections.abc import Generator, Sequence
from contextlib import contextmanager
from typing import Any
import structlog

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor, SpanExporter, SpanExportResult

logger = structlog.get_logger(__name__)


class InMemorySpanExporter(SpanExporter):
    """In-memory OpenTelemetry span exporter for unit testing and inspection."""

    def __init__(self) -> None:
        self._spans: list[ReadableSpan] = []

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Store exported spans in memory list."""
        self._spans.extend(spans)
        return SpanExportResult.SUCCESS

    def get_finished_spans(self) -> list[ReadableSpan]:
        """Return all finished spans captured in memory."""
        return list(self._spans)

    def clear(self) -> None:
        """Clear captured spans."""
        self._spans.clear()

    def shutdown(self) -> None:
        """Shutdown exporter and clear spans."""
        self._spans.clear()


# Global InMemorySpanExporter instance for test inspection
in_memory_exporter = InMemorySpanExporter()


class TelemetryService:
    """Service for initializing OpenTelemetry distributed tracing and span management."""

    def __init__(self, service_name: str = "ai-codeguardian", in_memory: bool = False) -> None:
        """Initialize TelemetryService with OpenTelemetry TracerProvider.

        Args:
            service_name: Name of the service for trace resource attributes.
            in_memory: If True, uses InMemorySpanExporter for test verification.
        """
        self.service_name = service_name
        self.resource = Resource.create({SERVICE_NAME: self.service_name})
        self.provider = TracerProvider(resource=self.resource)

        if in_memory:
            self.processor = SimpleSpanProcessor(in_memory_exporter)
        else:
            self.processor = BatchSpanProcessor(ConsoleSpanExporter())

        self.provider.add_span_processor(self.processor)
        trace.set_tracer_provider(self.provider)
        self.tracer = trace.get_tracer(self.service_name)
        logger.info("opentelemetry_telemetry_initialized", service_name=self.service_name)

    def get_tracer(self, name: str | None = None) -> trace.Tracer:
        """Get an OpenTelemetry Tracer instance.

        Args:
            name: Optional name for tracer scope.

        Returns:
            OpenTelemetry Tracer instance.
        """
        return trace.get_tracer(name or self.service_name)

    @contextmanager
    def start_span(
        self, span_name: str, attributes: dict[str, Any] | None = None
    ) -> Generator[trace.Span, None, None]:
        """Context manager to start and automatically close a trace span.

        Args:
            span_name: Name of the trace span.
            attributes: Optional key-value span attributes.

        Yields:
            Active trace.Span instance.
        """
        with self.tracer.start_as_current_span(span_name) as span:
            if attributes:
                for key, val in attributes.items():
                    span.set_attribute(key, str(val))
            yield span


# Global Telemetry Instance
telemetry_service = TelemetryService(in_memory=True)
