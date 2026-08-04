from typing import Any
import structlog

logger = structlog.get_logger(__name__)

# Flag indicating whether Sentry was initialized
_sentry_initialized = False


def init_sentry(
    dsn: str | None = None,
    environment: str = "production",
    traces_sample_rate: float = 0.1,
) -> bool:
    """Initialize Sentry exception tracking SDK with FastAPI and Celery integrations.

    Args:
        dsn: Sentry Data Source Name URL. If None, Sentry is disabled gracefully.
        environment: Deployment environment name ('production', 'staging', 'development').
        traces_sample_rate: Performance tracing sample rate (0.0 to 1.0).

    Returns:
        True if Sentry SDK was successfully initialized, else False.
    """
    global _sentry_initialized

    if not dsn:
        logger.info("sentry_disabled_no_dsn")
        _sentry_initialized = False
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            integrations=[
                FastApiIntegration(),
                CeleryIntegration(),
            ],
        )
        _sentry_initialized = True
        logger.info("sentry_initialized_successfully", environment=environment)
        return True
    except Exception as exc:
        logger.warning("sentry_initialization_failed", error=str(exc))
        _sentry_initialized = False
        return False


def capture_exception(exc: Exception, tags: dict[str, Any] | None = None) -> None:
    """Capture exception and report to Sentry if initialized.

    Args:
        exc: Exception instance to log and capture.
        tags: Optional key-value tags.
    """
    if _sentry_initialized:
        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                if tags:
                    for k, v in tags.items():
                        scope.set_tag(k, str(v))
                sentry_sdk.capture_exception(exc)
        except Exception as err:
            logger.warning("sentry_capture_failed", error=str(err))
    logger.error("captured_exception", error=str(exc))
