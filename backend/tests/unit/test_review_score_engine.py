from app.review_engine.finding import Finding
from app.review_engine.scoring import (
    ReviewScoreEngine,
    ReviewScoreReport,
    ScoreCalculator,
)


def test_perfect_score() -> None:
    """Verify 0 findings produces a 100.0 score, A+ grade, Perfect label, and Passed True."""
    engine = ReviewScoreEngine()
    report = engine.calculate_score([])

    assert isinstance(report, ReviewScoreReport)
    assert report.score == 100.0
    assert report.grade == "A+"
    assert report.risk_label == "Perfect"
    assert report.passed is True
    assert report.total_deductions == 0.0
    assert report.critical_cap_applied is False


def test_minor_issue_score_range() -> None:
    """Verify single low-severity finding yields 90.0-99.9 score range and Grade A."""
    engine = ReviewScoreEngine()
    finding = Finding(
        source="ai:clean_code",
        category="clean_code",
        severity="low",
        title="Unused Variable",
        description="Local variable declared but unused.",
    )

    report = engine.calculate_score([finding])

    assert 90.0 <= report.score < 100.0
    assert report.grade == "A"
    assert report.risk_label == "Minor Issue"
    assert report.passed is True


def test_medium_issue_score_range() -> None:
    """Verify medium-severity findings yield 70.0-89.9 score range and Grade B."""
    engine = ReviewScoreEngine()
    findings = [
        Finding(
            source="rule_engine",
            category="testing",
            severity="medium",
            title="Missing Test Case",
            description="New API endpoint lacks integration test.",
        ),
        Finding(
            source="ai:clean_code",
            category="clean_code",
            severity="medium",
            title="Magic Number",
            description="Hardcoded magic constant found.",
        ),
    ]

    report = engine.calculate_score(findings)

    assert 70.0 <= report.score < 90.0
    assert report.grade == "B"
    assert report.risk_label == "Medium Issue"
    assert report.passed is True


def test_serious_issue_score_range() -> None:
    """Verify high-severity findings yield 40.0-69.9 score range and Grade C."""
    engine = ReviewScoreEngine()
    findings = [
        Finding(
            source="ai:performance",
            category="performance",
            severity="high",
            title="N+1 Database Query",
            description="Query executed inside loop.",
        ),
        Finding(
            source="ai:architecture",
            category="architecture",
            severity="high",
            title="Tight Coupling",
            description="Direct dependency on concrete database class.",
        ),
    ]

    report = engine.calculate_score(findings)

    assert 40.0 <= report.score < 70.0
    assert report.grade == "C"
    assert report.risk_label == "Serious Issue"
    assert report.passed is False


def test_dangerous_code_score_range() -> None:
    """Verify multiple critical findings force score to 0.0, Grade F, and Dangerous Code."""
    engine = ReviewScoreEngine()
    findings = [
        Finding(
            source="ai:security",
            category="security",
            severity="critical",
            title="SQL Injection Vulnerability",
            description="Unsanitized SQL query string concatenation.",
        ),
        Finding(
            source="ai:security",
            category="security",
            severity="critical",
            title="Hardcoded API Secret",
            description="Production private token found in repository.",
        ),
    ]

    report = engine.calculate_score(findings)

    assert report.score == 0.0
    assert report.grade == "F"
    assert report.risk_label == "Dangerous Code"
    assert report.passed is False
    assert report.critical_cap_applied is True


def test_single_critical_finding_safety_cap() -> None:
    """Verify a single critical finding caps score to max 40.0 regardless of preliminary deductions."""
    engine = ReviewScoreEngine()
    critical_finding = Finding(
        source="ai:security",
        category="security",
        severity="critical",
        title="Unsafe Deserialization",
        description="Pickle load called on raw socket bytes.",
    )

    report = engine.calculate_score([critical_finding])

    assert report.score <= 40.0
    assert report.critical_cap_applied is True
    assert report.passed is False


def test_category_weight_multipliers() -> None:
    """Verify security category (1.5x) incurs higher deduction than clean_code category (0.9x)."""
    engine = ReviewScoreEngine()

    sec_finding = Finding(
        source="ai:security",
        category="security",
        severity="high",
        title="CSRF Token Missing",
        description="POST endpoint lacks CSRF validation.",
    )
    clean_finding = Finding(
        source="ai:clean_code",
        category="clean_code",
        severity="high",
        title="Long Method",
        description="Method exceeds line limit.",
    )

    report_sec = engine.calculate_score([sec_finding])
    report_clean = engine.calculate_score([clean_finding])

    assert report_sec.total_deductions > report_clean.total_deductions
    assert report_sec.score < report_clean.score


def test_diminishing_returns_scaling() -> None:
    """Verify repeated findings of the same category and severity apply diminishing returns multiplier."""
    engine = ReviewScoreEngine()

    single_finding = Finding(
        source="ai", category="testing", severity="medium", title="Issue 1", description="d"
    )
    three_findings = [
        Finding(
            source="ai",
            category="testing",
            severity="medium",
            title=f"Issue {i}",
            description="d",
        )
        for i in range(3)
    ]

    rep1 = engine.calculate_score([single_finding])
    rep3 = engine.calculate_score(three_findings)

    # Deduction for 3 items should be less than 3 * single item deduction due to 0.85 diminishing factor
    assert rep3.total_deductions < (rep1.total_deductions * 3)


def test_score_calculator_backwards_compatibility() -> None:
    """Verify ScoreCalculator delegates cleanly to ReviewScoreEngine."""
    calculator = ScoreCalculator()
    finding = Finding(
        source="ai", category="clean_code", severity="low", title="t", description="d"
    )

    score = calculator.calculate([finding])
    assert isinstance(score, float)
    assert 90.0 <= score < 100.0
