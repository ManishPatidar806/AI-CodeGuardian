from app.review_engine.context import ReviewContext
from app.review_engine.finding import Finding
from app.review_engine.rules.base import ReviewRule


class PRHygieneRule(ReviewRule):
    name = "pr_hygiene"

    MAX_CHANGED_FILES = 30
    MIN_DESCRIPTION_LENGTH = 20

    def evaluate(
        self,
        context: ReviewContext,
    ) -> list[Finding]:
        findings: list[Finding] = []

        if len(context.title.strip()) < 5:
            findings.append(
                Finding(
                    source="rule_engine",
                    category="pr_hygiene",
                    severity="low",
                    title="Merge Request title is too short",
                    description=(
                        "The Merge Request title does not clearly describe the change."
                    ),
                    suggestion=(
                        "Use a concise title describing what the Merge Request changes."
                    ),
                )
            )

        description = (context.description or "").strip()

        if len(description) < self.MIN_DESCRIPTION_LENGTH:
            findings.append(
                Finding(
                    source="rule_engine",
                    category="pr_hygiene",
                    severity="low",
                    title="Merge Request description is insufficient",
                    description=(
                        "The Merge Request should explain what changed and why."
                    ),
                    suggestion=(
                        "Add a description covering the purpose, "
                        "implementation, and relevant testing."
                    ),
                )
            )

        changed_files = len(context.diffs)

        if changed_files > self.MAX_CHANGED_FILES:
            findings.append(
                Finding(
                    source="rule_engine",
                    category="pr_size",
                    severity="medium",
                    title="Merge Request is too large",
                    description=(f"This Merge Request changes {changed_files} files."),
                    suggestion=(
                        "Consider splitting the change into smaller Merge Requests."
                    ),
                )
            )

        return findings
