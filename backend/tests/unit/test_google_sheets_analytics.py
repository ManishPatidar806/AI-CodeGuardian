from unittest.mock import MagicMock
import httpx
import pytest

from app.integrations.google_sheets.client import (
    GoogleSheetsAnalyticsService,
    GoogleSheetsMetricRow,
)


def test_google_sheets_metric_row_formatting() -> None:
    """Verify GoogleSheetsMetricRow attribute formatting and list/dict conversion."""
    row = GoogleSheetsMetricRow(
        repository="owner/ai-codeguardian",
        developer="alice_staff_dev",
        score=94.555,
        findings_count=2,
        review_time_ms=1240.456,
        cost_usd=0.0012345,
        date="2026-08-04T00:00:00Z",
    )

    assert row.repository == "owner/ai-codeguardian"
    assert row.developer == "alice_staff_dev"
    assert row.date == "2026-08-04T00:00:00Z"

    # Test .to_list()
    row_list = row.to_list()
    assert len(row_list) == 7
    assert row_list[0] == "owner/ai-codeguardian"
    assert row_list[1] == "alice_staff_dev"
    assert row_list[2] == 94.56
    assert row_list[3] == 2
    assert row_list[4] == 1240.46
    assert row_list[5] == pytest.approx(0.001235, abs=1e-5)
    assert row_list[6] == "2026-08-04T00:00:00Z"

    # Test .to_dict()
    row_dict = row.to_dict()
    assert row_dict["repository"] == "owner/ai-codeguardian"
    assert row_dict["findings_count"] == 2


def test_google_sheets_unconfigured_webhook_fallback() -> None:
    """Verify GoogleSheetsAnalyticsService handles unconfigured webhook URL gracefully."""
    service = GoogleSheetsAnalyticsService(webhook_url="")
    row = GoogleSheetsMetricRow(
        repository="owner/repo",
        developer="bob",
        score=85.0,
        findings_count=1,
        review_time_ms=500.0,
        cost_usd=0.0005,
    )

    result = service.append_review_metric(row)
    assert result is True


def test_google_sheets_append_review_metric_success() -> None:
    """Verify HTTP POST metric append operation with mocked httpx.Client."""
    mock_http_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_http_client.post.return_value = mock_response

    service = GoogleSheetsAnalyticsService(
        webhook_url="https://script.google.com/macros/s/test/exec",
        spreadsheet_id="sheet_12345",
        http_client=mock_http_client,
    )

    row = GoogleSheetsMetricRow(
        repository="owner/repo",
        developer="charlie",
        score=98.0,
        findings_count=0,
        review_time_ms=300.0,
        cost_usd=0.0002,
        date="2026-08-04T00:00:00Z",
    )

    result = service.append_review_metric(row)
    assert result is True
    mock_http_client.post.assert_called_once()


def test_google_sheets_batch_append_metrics() -> None:
    """Verify batch metric row export."""
    mock_http_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_http_client.post.return_value = mock_response

    service = GoogleSheetsAnalyticsService(
        webhook_url="https://script.google.com/macros/s/test/exec",
        spreadsheet_id="sheet_12345",
        http_client=mock_http_client,
    )

    rows = [
        GoogleSheetsMetricRow("r1", "d1", 90.0, 1, 100.0, 0.001),
        GoogleSheetsMetricRow("r2", "d2", 80.0, 2, 200.0, 0.002),
    ]

    exported = service.batch_append_metrics(rows)
    assert exported == 2
    assert mock_http_client.post.call_count == 2


def test_google_sheets_http_error_handling() -> None:
    """Verify error handling when Google Sheets HTTP API returns an error."""
    mock_http_client = MagicMock(spec=httpx.Client)
    mock_http_client.post.side_effect = httpx.HTTPError("500 Internal Server Error")

    service = GoogleSheetsAnalyticsService(
        webhook_url="https://script.google.com/macros/s/test/exec",
        http_client=mock_http_client,
    )

    row = GoogleSheetsMetricRow("r1", "d1", 50.0, 5, 800.0, 0.005)
    result = service.append_review_metric(row)
    assert result is False
