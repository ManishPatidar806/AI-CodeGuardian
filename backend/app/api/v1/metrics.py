from fastapi import APIRouter, Response

from app.core.metrics import metrics_service

router = APIRouter(tags=["Metrics"])


@router.get("/metrics", summary="Prometheus Metrics Endpoint")
def get_prometheus_metrics() -> Response:
    """Expose application metrics in Prometheus exposition format."""
    content, media_type = metrics_service.generate_metrics_exposition()
    return Response(content=content, media_type=media_type)
