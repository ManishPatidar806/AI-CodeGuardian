import json
from pathlib import Path
from typing import Any
import structlog

logger = structlog.get_logger(__name__)


class GrafanaDashboardService:
    """Service for loading, validating, and managing Grafana dashboard configurations."""

    def __init__(self, dashboard_path: str | Path | None = None) -> None:
        """Initialize GrafanaDashboardService.

        Args:
            dashboard_path: Optional path to the Grafana dashboard JSON file.
        """
        if dashboard_path:
            self.dashboard_path = Path(dashboard_path)
        else:
            # Default path relative to repository root
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.dashboard_path = base_dir / "grafana" / "dashboards" / "ai_codeguardian_dashboard.json"

    def load_dashboard_json(self) -> dict[str, Any]:
        """Load and parse Grafana dashboard JSON configuration.

        Returns:
            Dictionary payload of Grafana dashboard schema.

        Raises:
            FileNotFoundError: If the dashboard file does not exist.
            ValueError: If JSON is invalid.
        """
        if not self.dashboard_path.exists():
            logger.error("grafana_dashboard_file_not_found", path=str(self.dashboard_path))
            raise FileNotFoundError(f"Grafana dashboard file not found at {self.dashboard_path}")

        try:
            with open(self.dashboard_path, "r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
            return data
        except Exception as exc:
            logger.error("grafana_dashboard_parse_error", error=str(exc))
            raise ValueError(f"Failed to parse Grafana dashboard JSON: {exc}") from exc

    def validate_dashboard_schema(self, data: dict[str, Any] | None = None) -> bool:
        """Validate Grafana dashboard JSON schema integrity.

        Args:
            data: Optional dashboard data dictionary. If omitted, loads from file.

        Returns:
            True if schema is valid, False otherwise.
        """
        if data is None:
            data = self.load_dashboard_json()

        required_keys = ["title", "panels", "schemaVersion", "uid"]
        for k in required_keys:
            if k not in data:
                logger.warning("grafana_validation_missing_key", missing_key=k)
                return False

        panels = data.get("panels", [])
        if not isinstance(panels, list) or len(panels) == 0:
            logger.warning("grafana_validation_no_panels")
            return False

        return True

    def get_panel_definitions(self) -> list[dict[str, Any]]:
        """Retrieve list of panel definitions from the loaded dashboard.

        Returns:
            List of panel dictionaries.
        """
        data = self.load_dashboard_json()
        panels: list[dict[str, Any]] = data.get("panels", [])
        return panels
