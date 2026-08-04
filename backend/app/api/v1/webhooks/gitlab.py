import secrets
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.session import get_db
from app.schemas.gitlab import (
    GitLabMergeRequestEvent,
    GitLabWebhookResponse,
)
from app.services.gitlab_webhook import GitLabWebhookService


router = APIRouter(
    prefix="/webhooks/gitlab",
    tags=["GitLab Webhooks"],
)

logger = structlog.get_logger(__name__)

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=GitLabWebhookResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def receive_gitlab_webhook(
    payload: GitLabMergeRequestEvent,
    db: DbSession,
    x_gitlab_token: Annotated[str | None, Header()] = None,
    x_gitlab_event: Annotated[str | None, Header()] = None,
) -> GitLabWebhookResponse:
    if x_gitlab_token is None or not secrets.compare_digest(
        x_gitlab_token,
        settings.gitlab_webhook_secret,
    ):
        logger.warning("gitlab_webhook_authentication_failed")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook token",
        )

    if x_gitlab_event != "Merge Request Hook":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported GitLab event",
        )
    if payload.object_kind != "merge_request":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload",
        )

    service = GitLabWebhookService(db)

    merge_request = service.process_merge_request(payload)

    return GitLabWebhookResponse(
        status="accepted",
        message="Merge request event processed",
        merge_request_id=merge_request.id,
    )
