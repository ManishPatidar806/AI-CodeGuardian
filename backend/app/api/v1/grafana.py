from typing import Any
from fastapi import APIRouter, HTTPException

from app.services.grafana_service import GrafanaDashboardService

router = APIRouter(prefix="/grafana", tags=["Grafana"])
grafana_service = GrafanaDashboardService()


@router.get("/dashboard", summary="Grafana Dashboard JSON Provisioning Endpoint")
def get_grafana_dashboard() -> dict[str, Any]:
    """Expose Grafana dashboard JSON configuration for automated Grafana provisioning or API import."""
    try:
        return grafana_service.load_dashboard_json()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve Grafana dashboard configuration: {exc}",
        ) from exc
