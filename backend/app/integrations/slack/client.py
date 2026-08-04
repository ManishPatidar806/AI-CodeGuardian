from typing import Any
import httpx
import structlog

from app.core.settings import settings

logger = structlog.get_logger(__name__)


class SlackClient:
    """HTTP client for dispatching Slack notifications via Webhooks or Bot REST API."""

    def __init__(
        self,
        bot_token: str | None = None,
        webhook_url: str | None = None,
    ) -> None:
        """Initialize SlackClient.

        Args:
            bot_token: Optional Slack bot user OAuth token (xoxb-...).
            webhook_url: Optional Slack incoming webhook URL.
        """
        self.bot_token = bot_token or getattr(settings, "slack_bot_token", "")
        self.webhook_url = webhook_url or getattr(settings, "slack_webhook_url", "")

        headers = {"Content-Type": "application/json"}
        if self.bot_token:
            headers["Authorization"] = f"Bearer {self.bot_token}"

        self.client = httpx.Client(
            base_url="https://slack.com/api",
            headers=headers,
            timeout=15.0,
        )

    def post_message(
        self,
        channel: str,
        blocks: list[dict[str, Any]],
        fallback_text: str = "AI CodeGuardian Review Notification",
    ) -> dict[str, Any]:
        """Post a Block Kit formatted message to a Slack channel or webhook.

        Args:
            channel: Target Slack channel name or ID (e.g. '#code-reviews' or 'C123456').
            blocks: List of Slack Block Kit block dictionaries.
            fallback_text: Plain text fallback string for notifications.

        Returns:
            API response dictionary from Slack.

        Raises:
            httpx.HTTPError: If Slack API request fails.
        """
        logger.info("slack_posting_message", channel=channel, blocks_count=len(blocks))

        if self.webhook_url:
            # Dispatch via Incoming Webhook
            payload = {
                "text": fallback_text,
                "blocks": blocks,
            }
            if channel and not channel.startswith("http"):
                payload["channel"] = channel

            response = httpx.post(
                self.webhook_url,
                json=payload,
                timeout=15.0,
            )
            response.raise_for_status()
            return {"ok": True, "source": "webhook"}

        if self.bot_token:
            # Dispatch via Slack REST API chat.postMessage
            payload = {
                "channel": channel,
                "text": fallback_text,
                "blocks": blocks,
            }
            response = self.client.post("/chat.postMessage", json=payload)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                error_msg = data.get("error", "Unknown Slack API error")
                logger.error("slack_api_error", error=error_msg, channel=channel)
                raise RuntimeError(f"Slack API error: {error_msg}")

            return data

        logger.warning("slack_credentials_not_configured")
        return {"ok": False, "message": "Slack bot token or webhook URL not configured"}

    def close(self) -> None:
        """Close HTTP client session."""
        self.client.close()
