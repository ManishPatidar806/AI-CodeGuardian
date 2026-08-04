import logging
import sys

import structlog

from app.core.settings import settings


def configure_logging() -> None:
    """Configure application-wide structured logging."""

    logging.basicConfig(
        level=settings.log_level,
        format="%(message)s",
        stream=sys.stdout,
        force=True,
    )

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    renderer = (
        structlog.dev.ConsoleRenderer()
        if settings.app_env == "development"
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[
            *shared_processors,
            renderer,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
