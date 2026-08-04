import hmac
from fastapi import Header, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
import structlog

from app.core.settings import settings

logger = structlog.get_logger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """FastAPI security dependency enforcing X-API-Key authentication for admin APIs.

    Args:
        api_key: X-API-Key header value.

    Returns:
        Validated API key string.

    Raises:
        HTTPException 401 if API key is invalid or missing.
    """
    expected_key = getattr(settings, "API_KEY", "dev-secret-api-key")

    if not api_key or not hmac.compare_digest(api_key, expected_key):
        logger.warning("unauthorized_api_key_access_attempt", provided_key=api_key)
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing X-API-Key header.",
        )

    return api_key


def verify_gitlab_webhook_signature(
    x_gitlab_token: str | None = Header(default=None, alias="X-Gitlab-Token")
) -> bool:
    """Verify GitLab webhook token header against configured secret.

    Args:
        x_gitlab_token: X-Gitlab-Token header value.

    Returns:
        True if webhook signature matches.

    Raises:
        HTTPException 401 if token is invalid or missing.
    """
    expected_secret = getattr(settings, "GITLAB_WEBHOOK_SECRET", "dev-secret-token")

    if not x_gitlab_token or not hmac.compare_digest(x_gitlab_token, expected_secret):
        logger.warning("invalid_gitlab_webhook_token")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid X-Gitlab-Token webhook signature.",
        )

    return True
