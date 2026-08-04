from dataclasses import dataclass, field
from typing import Sequence

import structlog

from app.review_engine.finding import Finding

logger = structlog.get_logger(__name__)

# Base penalty points subtracted per severity level
SEVERITY_BASE_PENALTIES: dict[str, float] = {
    "critical": 45.0,
    "high": 20.0,
    "medium": 10.0,
    "low": 3.0,
    "info": 0.0,
}

# Category weight multipliers (e.g. Security issues carry 1.5x penalty)
CATEGORY_WEIGHT_MULTIPLIERS: dict[str, float] = {
    "security": 1.5,
    "performance": 1.2,
    "architecture": 1.1,
    "testing": 1.0,
    "clean_code": 0.9,
    "maintainability": 0.9,
    "general": 1.0,
}


@dataclass
class ReviewScoreReport:
    """Detailed score evaluation report produced by ReviewScoreEngine.

    Attributes:
        score: Final calculated quality score (0.0 to 100.0).
        grade: Letter grade assessment ('A+', 'A', 'B', 'C', 'F').
        risk_label: Qualitative risk description ('Perfect', 'Minor Issue', 'Medium Issue', 'Serious Issue', 'Dangerous Code').
        passed: Boolean indicating if the review score meets the minimum quality bar (score >= 70.0 and no critical issues).
        total_deductions: Sum of all weighted penalties subtracted from 100.0.
        severity_deductions: Deductions breakdown grouped by severity.
        category_deductions: Deductions breakdown grouped by category.
        critical_cap_applied: True if a safety floor/cap was triggered by critical findings.
    """

    score: float
    grade: str
    risk_label: str
    passed: bool
    total_deductions: float = 0.0
    severity_deductions: dict[str, float] = field(default_factory=dict)
    category_deductions: dict[str, float] = field(default_factory=dict)
    critical_cap_applied: bool = False


class ReviewScoreEngine:
    """Enterprise weighted scoring engine for code reviews.

    The ReviewScoreEngine forms Phase 6 of the AI CodeGuardian pipeline.
    It evaluates Findings and computes a quality score from 0.0 to 100.0:
    - 100.0: Perfect (0 issues)
    - 90.0 - 99.9: Minor Issue (Low Risk)
    - 70.0 - 89.9: Medium Issue (Moderate Risk)
    - 40.0 - 69.9: Serious Issue (High Risk)
    - 0.0 - 39.9: Dangerous Code (Critical Risk / Unacceptable)

    Key Features:
    - Weighted severity (Critical > High > Medium > Low > Info)
    - Category weighting (Security 1.5x > Performance 1.2x > Style 0.9x)
    - Diminishing returns scaling for repeated duplicate findings
    - Safety floor capping: 1 critical finding caps max score to 40.0; 2+ critical findings drop score to 0.0.
    """

    def __init__(
        self,
        base_penalties: dict[str, float] | None = None,
        category_multipliers: dict[str, float] | None = None,
        diminishing_factor: float = 0.85,
        min_pass_score: float = 70.0,
    ) -> None:
        """Initialize ReviewScoreEngine.

        Args:
            base_penalties: Optional custom severity base penalties.
            category_multipliers: Optional custom category multipliers.
            diminishing_factor: Factor applied to repeated findings of the same severity/category.
            min_pass_score: Minimum numerical score required to pass review.
        """
        self.base_penalties = base_penalties or SEVERITY_BASE_PENALTIES
        self.category_multipliers = category_multipliers or CATEGORY_WEIGHT_MULTIPLIERS
        self.diminishing_factor = diminishing_factor
        self.min_pass_score = min_pass_score

    def calculate_score(
        self,
        findings: Sequence[Finding] | None = None,
    ) -> ReviewScoreReport:
        """Calculate quality score, grade, risk label, and deduction breakdown from findings.

        Args:
            findings: Sequence of Finding objects.

        Returns:
            ReviewScoreReport containing score, grade, risk label, and detailed breakdown.
        """
        raw_findings = list(findings or [])
        if not raw_findings:
            logger.info("review_score_engine_zero_findings")
            return ReviewScoreReport(
                score=100.0,
                grade="A+",
                risk_label="Perfect",
                passed=True,
                total_deductions=0.0,
                severity_deductions={"critical": 0.0, "high": 0.0, "medium": 0.0, "low": 0.0, "info": 0.0},
                category_deductions={},
                critical_cap_applied=False,
            )

        logger.debug("review_score_engine_started", finding_count=len(raw_findings))

        # Track occurrence counts for diminishing returns
        occurrence_counts: dict[tuple[str, str], int] = {}
        severity_deductions: dict[str, float] = {
            "critical": 0.0,
            "high": 0.0,
            "medium": 0.0,
            "low": 0.0,
            "info": 0.0,
        }
        category_deductions: dict[str, float] = {}
        total_deductions = 0.0
        critical_count = 0

        for finding in raw_findings:
            sev = finding.severity.strip().lower()
            cat = finding.category.strip().lower()

            if sev == "critical":
                critical_count += 1

            base_penalty = self.base_penalties.get(sev, 10.0)
            cat_multiplier = self.category_multipliers.get(cat, 1.0)

            # Diminishing returns scaling for repeated issues
            key = (sev, cat)
            occurrence = occurrence_counts.get(key, 0) + 1
            occurrence_counts[key] = occurrence

            diminish_multiplier = self.diminishing_factor ** (occurrence - 1)
            finding_penalty = base_penalty * cat_multiplier * diminish_multiplier

            total_deductions += finding_penalty
            severity_deductions[sev] = severity_deductions.get(sev, 0.0) + finding_penalty
            category_deductions[cat] = category_deductions.get(cat, 0.0) + finding_penalty

        # Compute preliminary score
        preliminary_score = max(0.0, 100.0 - total_deductions)
        final_score = preliminary_score
        critical_cap_applied = False

        # Apply Safety Floor rules for critical vulnerabilities
        if critical_count >= 2:
            # 2+ Critical vulnerabilities -> Forced 0.0 (Dangerous Code)
            final_score = 0.0
            critical_cap_applied = True
        elif critical_count == 1:
            # 1 Critical vulnerability -> Score capped at max 40.0 (Serious Issue)
            if final_score > 40.0:
                final_score = 40.0
            critical_cap_applied = True

        final_score = max(0.0, min(100.0, round(final_score, 2)))
        total_deductions = round(total_deductions, 2)

        grade, risk_label = self._map_score_to_grade_and_risk(final_score, critical_count)
        passed = final_score >= self.min_pass_score and critical_count == 0

        logger.info(
            "review_score_engine_completed",
            score=final_score,
            grade=grade,
            risk_label=risk_label,
            critical_count=critical_count,
            critical_cap_applied=critical_cap_applied,
        )

        return ReviewScoreReport(
            score=final_score,
            grade=grade,
            risk_label=risk_label,
            passed=passed,
            total_deductions=total_deductions,
            severity_deductions={k: round(v, 2) for k, v in severity_deductions.items()},
            category_deductions={k: round(v, 2) for k, v in category_deductions.items()},
            critical_cap_applied=critical_cap_applied,
        )

    def _map_score_to_grade_and_risk(
        self, score: float, critical_count: int
    ) -> tuple[str, str]:
        """Map numerical score to letter grade and risk label.

        Scale:
        - 100.0: Grade A+ | Perfect
        - 90.0 - 99.9: Grade A | Minor Issue
        - 70.0 - 89.9: Grade B | Medium Issue
        - 40.0 - 69.9: Grade C | Serious Issue
        - 0.0 - 39.9: Grade F | Dangerous Code

        Args:
            score: Numerical score (0.0 to 100.0).
            critical_count: Number of critical findings.

        Returns:
            Tuple of (grade_string, risk_label_string).
        """
        if critical_count >= 2 or score < 40.0:
            return "F", "Dangerous Code"
        if score == 100.0:
            return "A+", "Perfect"
        if score >= 90.0:
            return "A", "Minor Issue"
        if score >= 70.0:
            return "B", "Medium Issue"
        return "C", "Serious Issue"


class ScoreCalculator:
    """Backwards-compatible wrapper delegating to ReviewScoreEngine."""

    STARTING_SCORE = 100.0
    PENALTIES = {
        "low": 5.0,
        "medium": 10.0,
        "high": 20.0,
        "critical": 40.0,
    }

    def __init__(self) -> None:
        self.engine = ReviewScoreEngine()

    def calculate(
        self,
        findings: list[Finding],
    ) -> float:
        """Calculate simple numerical score for backwards compatibility.

        Args:
            findings: List of Finding objects.

        Returns:
            Calculated score.
        """
        report = self.engine.calculate_score(findings)
        return report.score
