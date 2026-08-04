from typing import Any, Sequence

from app.review_engine.finding import Finding


class SlackBlockKitBuilder:
    """Builds rich Slack Block Kit JSON layouts for code review reports."""

    def build_review_notification_blocks(
        self,
        repository: str,
        developer: str,
        score: float,
        grade: str,
        summary: str,
        top_findings: Sequence[Finding],
        mr_url: str | None = None,
        mr_title: str | None = None,
        branch_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Construct Slack Block Kit UI blocks for an AI review report.

        Args:
            repository: Repository name or path_with_namespace.
            developer: Developer username or author name.
            score: Overall review score (0.0 to 100.0).
            grade: Letter grade assessment ('A+', 'A', 'B', 'C', 'F').
            summary: Short review summary string.
            top_findings: List of top Finding objects to highlight.
            mr_url: Merge Request URL link.
            mr_title: Merge Request title.
            branch_name: Source branch name.

        Returns:
            List of Slack Block Kit block dictionaries.
        """
        score_emoji = "✅" if score >= 80.0 else ("⚠️" if score >= 50.0 else "❌")

        blocks: list[dict[str, Any]] = [
            # 1. Header Block
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{score_emoji} AI CodeGuardian Review Report",
                    "emoji": True,
                },
            },
            # 2. Key Metadata Section (Repository, Developer, Score, Grade)
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Repository:*\n`{repository}`",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Developer:*\n`@{developer}`",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Quality Score:*\n`{score:.1f} / 100.0` (Grade: *{grade}*)",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{'*Approved*' if score >= 80.0 else '*Changes Requested*'}",
                    },
                ],
            },
        ]

        # 3. Add MR Title if provided
        if mr_title:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Merge Request:* {mr_title}",
                    },
                }
            )

        # 4. Executive Summary Section
        cleaned_summary = summary.strip().split("\n\n")[0] if summary else "Review completed."
        if len(cleaned_summary) > 400:
            cleaned_summary = cleaned_summary[:400] + "..."

        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Review Summary:*\n{cleaned_summary}",
                },
            }
        )

        blocks.append({"type": "divider"})

        # 5. Top Findings Section
        raw_findings = list(top_findings or [])
        if raw_findings:
            finding_lines: list[str] = ["*Top Priority Findings:*"]
            for idx, f in enumerate(raw_findings[:5], 1):
                sev_icon = {
                    "critical": "🚨",
                    "high": "⚠️",
                    "medium": "🟡",
                    "low": "🔹",
                    "info": "ℹ️",
                }.get(f.severity.lower(), "🔍")

                location = (
                    f"`{f.file_path}:{f.line_number}`"
                    if f.file_path and f.line_number
                    else (f"`{f.file_path}`" if f.file_path else "Global")
                )
                finding_lines.append(
                    f"{idx}. {sev_icon} *{f.title}* ({location})\n   _{f.description[:150]}_"
                )

            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(finding_lines),
                    },
                }
            )
        else:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Top Findings:*\n🎉 No critical or high severity issues detected!",
                    },
                }
            )

        blocks.append({"type": "divider"})

        # 6. Action Button Block (MR Link)
        if mr_url:
            blocks.append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔗 View Merge Request in GitLab",
                                "emoji": True,
                            },
                            "url": mr_url,
                            "style": "primary" if score >= 80.0 else "danger",
                        }
                    ],
                }
            )

        # 7. Context Footer Block
        branch_str = f" • Branch: `{branch_name}`" if branch_name else ""
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🛡️ AI CodeGuardian Bot{branch_str}",
                    }
                ],
            }
        )

        return blocks
