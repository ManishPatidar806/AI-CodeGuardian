from fastapi import APIRouter
from app.api.v1.config import router as config_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.fix_generator import router as fix_generator_router
from app.api.v1.grafana import router as grafana_router
from app.api.v1.health import router as health_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.repositories import router as repositories_router
from app.api.v1.users import router as users_router
from app.api.v1.webhooks.gitlab import router as gitlab_webhook_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(metrics_router)
api_router.include_router(grafana_router)
api_router.include_router(dashboard_router)
api_router.include_router(config_router)
api_router.include_router(repositories_router)
api_router.include_router(users_router)
api_router.include_router(fix_generator_router)
api_router.include_router(gitlab_webhook_router)

