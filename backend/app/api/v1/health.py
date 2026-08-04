from typing import Literal, Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.settings import settings
from app.db.session import get_db


DbSession = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    app_name: str
    version: str
    environment: str
    database: Literal["connected"]


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check application health",
)
def health_check(db: DbSession) -> HealthResponse:
    db.execute(text("SELECT 1"))
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        database="connected",
    )
