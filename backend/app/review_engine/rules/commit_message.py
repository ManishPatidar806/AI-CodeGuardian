import re

from app.review_engine.context import ReviewContext
from app.review_engine.finding import Finding
from app.review_engine.rules.base import ReviewRule


class CommitMessageRule(ReviewRule):
    name = "commit_message"

    _pattern = re.compile(
        r"^(feat|fix|docs|style|refactor|test|chore|perf|build|ci)"
        r"(?:\([a-z0-9_-]+\))?"
        r": .+"
    )

    def evaluate(
        self,
        context: ReviewContext,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for commit in context.commits:
            message = (commit.get("title") or commit.get("message") or "").strip()

            if self._pattern.fullmatch(message):
                continue

            short_id = commit.get("short_id", "unknown")

            findings.append(
                Finding(
                    source="rule_engine",
                    category="commit_message",
                    severity="low",
                    title="Invalid commit message",
                    description=(
                        f"Commit '{short_id}' has an invalid message: '{message}'."
                    ),
                    suggestion=(
                        "Use Conventional Commits, for example "
                        "'feat: add authentication'."
                    ),
                )
            )

        return findings
