import structlog

from app.review_engine.context import ReviewContext
from app.review_engine.finding import Finding
from app.review_engine.rules.base import ReviewRule


logger = structlog.get_logger(__name__)


class ReviewEngine:
    def __init__(
        self,
        rules: list[ReviewRule],
    ) -> None:
        self.rules = rules

    def run(
        self,
        context: ReviewContext,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for rule in self.rules:
            logger.info(
                "review_rule_started",
                rule=rule.name,
                project_id=context.project_id,
                mr_iid=context.mr_iid,
            )

            rule_findings = rule.evaluate(context)

            findings.extend(rule_findings)

            logger.info(
                "review_rule_completed",
                rule=rule.name,
                findings=len(rule_findings),
            )

        return findings
