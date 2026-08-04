import re
from app.review_engine.context import ReviewContext
from app.review_engine.finding import Finding
from app.review_engine.rules.base import ReviewRule


class BranchNameRule(ReviewRule):
    name = "branch_name"

    _pattern = re.compile(
        r"^(feature|bugfix|hotfix|refactor)/"
        r"[A-Z][A-Z0-9]+-\d+-"
        r"[a-z0-9]+(?:-[a-z0-9]+)*$"
    )

    def evaluate(self, context: ReviewContext) -> list[Finding]:
        branch = context.source_branch

        if self._pattern.fullmatch(branch):
            return []

        return [
            Finding(
                source="rule_engine",
                category="branch_naming",
                severity="medium",
                title="Invalid branch name",
                description=(
                    f"Branch '{branch}' does not follow"
                    "the required Jira-style naming convention."
                ),
                suggestion=(
                    "Use a branch name such as 'feature/CG-123-add-authentication'."
                ),
            )
        ]
