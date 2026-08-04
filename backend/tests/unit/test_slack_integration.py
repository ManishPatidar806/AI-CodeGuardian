from unittest.mock import MagicMock, patch

from app.integrations.slack.block_kit import SlackBlockKitBuilder
from app.integrations.slack.client import SlackClient
from app.integrations.slack.notifier import (
    ReviewNotificationPayload,
    SlackNotifier,
)
from app.review_engine.finding import Finding


def test_slack_block_kit_builder() -> None:
    """Verify SlackBlockKitBuilder constructs valid Slack Block Kit JSON blocks."""
    builder = SlackBlockKitBuilder()

    findings = [
        Finding(
            source="ai:security",
            category="security",
            severity="critical",
            title="SQL Injection Vulnerability",
            description="Raw query concatenation detected.",
            file_path="app/db/query.py",
            line_number=42,
        ),
        Finding(
            source="ai:performance",
            category="performance",
            severity="high",
            title="N+1 Query Issue",
            description="Query in loop.",
            file_path="app/user.py",
            line_number=10,
        ),
    ]

    blocks = builder.build_review_notification_blocks(
        repository="owner/repo",
        developer="mohit_dev",
        score=85.0,
        grade="B",
        summary="Review completed with 2 findings.",
        top_findings=findings,
        mr_url="https://gitlab.com/owner/repo/-/merge_requests/42",
        mr_title="Add new API endpoint",
        branch_name="feature/api",
    )

    assert isinstance(blocks, list)
    assert len(blocks) >= 6

    # 1. Header Block
    assert blocks[0]["type"] == "header"
    assert "AI CodeGuardian Review Report" in blocks[0]["text"]["text"]

    # 2. Section Block Fields
    fields = blocks[1]["fields"]
    assert any("`owner/repo`" in f["text"] for f in fields)
    assert any("`@mohit_dev`" in f["text"] for f in fields)
    assert any("`85.0 / 100.0`" in f["text"] for f in fields)

    # 3. Findings Section
    findings_block = next(b for b in blocks if "Top Priority Findings" in b.get("text", {}).get("text", ""))
    assert "SQL Injection Vulnerability" in findings_block["text"]["text"]
    assert "`app/db/query.py:42`" in findings_block["text"]["text"]

    # 4. Action Button
    action_block = next(b for b in blocks if b.get("type") == "actions")
    button = action_block["elements"][0]
    assert button["type"] == "button"
    assert button["url"] == "https://gitlab.com/owner/repo/-/merge_requests/42"


@patch("httpx.post")
def test_slack_client_webhook_dispatch(mock_httpx_post: MagicMock) -> None:
    """Verify SlackClient posts payload to webhook URL."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_httpx_post.return_value = mock_response

    client = SlackClient(webhook_url="https://hooks.slack.com/services/T00/B00/X00")
    res = client.post_message(
        channel="#code-reviews",
        blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Hello"}}],
        fallback_text="Fallback",
    )

    assert res["ok"] is True
    assert res["source"] == "webhook"
    mock_httpx_post.assert_called_once()


def test_slack_notifier_channel_override() -> None:
    """Verify channel_override takes precedence over default_channel."""
    mock_client = MagicMock(spec=SlackClient)
    mock_client.post_message.return_value = {"ok": True}

    notifier = SlackNotifier(
        slack_client=mock_client,
        default_channel="#default-channel",
    )

    payload = ReviewNotificationPayload(
        repository="owner/repo",
        developer="author",
        score=95.0,
        grade="A",
        summary="Summary",
        findings=[],
        mr_url="https://gitlab.com/mr/1",
        channel_override="#custom-alerts",
    )

    res = notifier.send_review_notification(payload)
    assert res["ok"] is True

    mock_client.post_message.assert_called_once()
    kwargs = mock_client.post_message.call_args.kwargs
    assert kwargs["channel"] == "#custom-alerts"


def test_slack_notifier_top_findings_spotlight() -> None:
    """Verify SlackNotifier filters top findings by severity order."""
    notifier = SlackNotifier()
    findings = [
        Finding(source="ai", category="c", severity="low", title="Low Issue", description="d"),
        Finding(source="ai", category="c", severity="critical", title="Critical Issue", description="d"),
        Finding(source="ai", category="c", severity="medium", title="Medium Issue", description="d"),
    ]

    top = notifier._get_top_findings(findings)
    assert len(top) == 3
    assert top[0].severity == "critical"
    assert top[1].severity == "medium"
    assert top[2].severity == "low"
