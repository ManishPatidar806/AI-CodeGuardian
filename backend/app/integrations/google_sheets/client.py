from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Sequence
import httpx
import structlog

from app.core.settings import settings

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class GoogleSheetsMetricRow:
    """Dataclass representing a single row of review metrics for Google Sheets export.

    Attributes:
        repository: Repository name or path_with_namespace.
        developer: Developer username or author name.
        score: Review quality score (0.0 to 100.0).
        findings_count: Total number of rule and AI findings.
        review_time_ms: Review duration in milliseconds.
        cost_usd: Estimated LLM cost in USD.
        date: ISO 8601 formatted date string (defaults to current UTC time).
    """

    repository: str
    developer: str
    score: float
    findings_count: int
    review_time_ms: float
    cost_usd: float
    date: str | None = None

    def __post_init__(self) -> None:
        if not self.date:
            object.__setattr__(
                self, "date", datetime.now(timezone.utc).isoformat()
            )

    def to_list(self) -> list[Any]:
        """Format metric row as a list matching spreadsheet column order.

        Column Order:
        1. Repository
        2. Developer
        3. Score
        4. Findings Count
        5. Review Time (ms)
        6. Cost (USD)
        7. Date
        """
        return [
            self.repository,
            self.developer,
            round(self.score, 2),
            self.findings_count,
            round(self.review_time_ms, 2),
            round(self.cost_usd, 6),
            self.date,
        ]

    def to_dict(self) -> dict[str, Any]:
        """Format metric row as a dictionary matching spreadsheet schema key-values."""
        return {
            "repository": self.repository,
            "developer": self.developer,
            "score": round(self.score, 2),
            "findings_count": self.findings_count,
            "review_time_ms": round(self.review_time_ms, 2),
            "cost_usd": round(self.cost_usd, 6),
            "date": self.date,
        }


class GoogleSheetsAnalyticsService:
    """Production service for exporting AI CodeGuardian review metrics to Google Sheets.

    Supports:
    1. Direct Webhook / Apps Script endpoint export via HTTP POST.
    2. Batch metric row processing.
    3. Graceful error handling for offline or unconfigured Sheets credentials.
    """

    HEADER_ROW = [
        "Repository",
        "Developer",
        "Score",
        "Findings Count",
        "Review Time (ms)",
        "Cost (USD)",
        "Date",
    ]

    def __init__(
        self,
        webhook_url: str | None = None,
        spreadsheet_id: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Initialize GoogleSheetsAnalyticsService.

        Args:
            webhook_url: Optional Google Apps Script or Webhook URL.
            spreadsheet_id: Optional Google Sheets Spreadsheet ID.
            http_client: Optional custom httpx.Client instance.
        """
        self.webhook_url = (
            webhook_url or getattr(settings, "google_sheets_webhook_url", "")
        )
        self.spreadsheet_id = (
            spreadsheet_id or getattr(settings, "google_sheets_spreadsheet_id", "")
        )
        self.client = http_client or httpx.Client(timeout=10.0)

    def append_review_metric(self, row: GoogleSheetsMetricRow) -> bool:
        """Append a single review metric row to Google Sheets.

        Args:
            row: GoogleSheetsMetricRow instance.

        Returns:
            True if exported successfully or handled cleanly, False on HTTP delivery failure.
        """
        if not self.webhook_url:
            logger.info(
                "google_sheets_webhook_not_configured_skipping_export",
                repository=row.repository,
                developer=row.developer,
            )
            return True

        payload = {
            "spreadsheet_id": self.spreadsheet_id,
            "row": row.to_list(),
            "data": row.to_dict(),
        }

        try:
            logger.info("exporting_metric_to_google_sheets", repository=row.repository, developer=row.developer)
            response = self.client.post(self.webhook_url, json=payload)
            response.raise_for_status()
            logger.info("exported_metric_to_google_sheets_success", status_code=response.status_code)
            return True
        except Exception as exc:
            logger.warning("google_sheets_export_failed", error=str(exc), repository=row.repository)
            return False

    def batch_append_metrics(self, rows: Sequence[GoogleSheetsMetricRow]) -> int:
        """Export multiple review metric rows to Google Sheets in a batch operation.

        Args:
            rows: Sequence of GoogleSheetsMetricRow instances.

        Returns:
            Count of successfully exported rows.
        """
        if not rows:
            return 0

        success_count = 0
        for r in rows:
            if self.append_review_metric(r):
                success_count += 1

        return success_count
