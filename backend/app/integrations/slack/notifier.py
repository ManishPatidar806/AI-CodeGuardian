from dataclasses import dataclass
from typing import Any, Sequence

import structlog

from app.core.settings import settings
from app.integrations.slack.block_kit import SlackBlockKitBuilder
from app.integrations.slack.client import SlackClient
from app.review_engine.finding import Finding

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ReviewNotificationPayload:
    """Payload model for dispatching Slack review notifications.

    Attributes:
        repository: Repository name or path_with_namespace.
        developer: Developer username or author name.
        score: Overall review score (0.0 to 100.0).
        grade: Letter grade ('A+', 'A', 'B', 'C', 'F').
        summary: Review summary string.
        findings: Sequence of Finding objects.
        mr_url: Merge Request URL.
        mr_title: Merge Request title.
        branch_name: Source branch name.
        channel_override: Optional custom target Slack channel.
    """

    repository: str
    developer: str
    score: float
    grade: str
    summary: str
    findings: Sequence[Finding]
    mr_url: str | None = None
    mr_title: str | None = None
    branch_name: str | None = None
    channel_override: str | None = None


class SlackNotifier:
    """High-level Slack notification service for AI CodeGuardian review reports.

    The SlackNotifier forms Phase 8 of the AI CodeGuardian pipeline.
    It builds Slack Block Kit layouts and dispatches formatted review notifications
    to configurable Slack channels.
    """

    def __init__(
        self,
        slack_client: SlackClient | None = None,
        block_builder: SlackBlockKitBuilder | None = None,
        default_channel: str | None = None,
    ) -> None:
        """Initialize SlackNotifier.

        Args:
            slack_client: Optional SlackClient instance.
            block_builder: Optional SlackBlockKitBuilder instance.
            default_channel: Optional default Slack channel (defaults to settings.slack_default_channel).
        """
        self.client = slack_client or SlackClient()
        self.block_builder = block_builder or SlackBlockKitBuilder()
        self.default_channel = (
            default_channel or getattr(settings, "slack_default_channel", "#code-reviews")
        )

    def send_review_notification(
        self,
        payload: ReviewNotificationPayload,
    ) -> dict[str, Any]:
        """Dispatch a formatted Block Kit review notification to Slack.

        Args:
            payload: ReviewNotificationPayload data object.

        Returns:
            Dictionary containing dispatch response status.
        """
        target_channel = payload.channel_override or self.default_channel

        logger.info(
            "slack_notifier_sending_report",
            repository=payload.repository,
            developer=payload.developer,
            score=payload.score,
            channel=target_channel,
        )

        # 1. Filter top priority findings for spotlight
        top_findings = self._get_top_findings(payload.findings)

        # 2. Construct Block Kit UI layout
        blocks = self.block_builder.build_review_notification_blocks(
            repository=payload.repository,
            developer=payload.developer,
            score=payload.score,
            grade=payload.grade,
            summary=payload.summary,
            top_findings=top_findings,
            mr_url=payload.mr_url,
            mr_title=payload.mr_title,
            branch_name=payload.branch_name,
        )

        fallback_text = (
            f"AI CodeGuardian Review for {payload.repository}: Score {payload.score:.1f}/100.0 (Grade: {payload.grade})"
        )

        # 3. Post message via SlackClient
        try:
            res = self.client.post_message(
                channel=target_channel,
                blocks=blocks,
                fallback_text=fallback_text,
            )
            logger.info(
                "slack_notifier_sent_successfully",
                channel=target_channel,
                score=payload.score,
            )
            return res
        except Exception as exc:
            logger.error(
                "slack_notifier_dispatch_failed",
                error=str(exc),
                channel=target_channel,
            )
            return {"ok": False, "error": str(exc)}

    def _get_top_findings(self, findings: Sequence[Finding]) -> list[Finding]:
        """Filter and rank top priority findings for Slack spotlight.

        Args:
            findings: Sequence of Finding objects.

        Returns:
            List of top findings sorted by severity.
        """
        sev_weights = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_findings = sorted(
            list(findings or []),
            key=lambda f: sev_weights.get(f.severity.lower(), 99),
        )
        return sorted_findings[:5]
