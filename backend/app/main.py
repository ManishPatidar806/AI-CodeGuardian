from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.logging import configure_logging
from app.core.settings import settings

configure_logging()

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )
    try:
        from app.db.base import Base
        from app.db.session import engine
        import app.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        logger.warning("database_auto_migration_skipped", error=str(exc))

    yield

    logger.info(
        "application_shutting_down",
        app_name=settings.app_name,
    )


def create_app() -> FastAPI:
    application = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.app_version,
        description=(
            ""
            "AI-powered intelligent pull request review "
            "and engineering automation platform."
        ),
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    application.include_router(
        api_router,
        prefix="/api/v1",
    )
    return application


app = create_app()
