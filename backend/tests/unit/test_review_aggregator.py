from app.review_engine.aggregator import (
    AggregatedReviewResult,
    ReviewAggregator,
)
from app.review_engine.finding import Finding
from app.review_engine.scoring import ScoreCalculator


def test_aggregate_empty_inputs() -> None:
    """Verify aggregation with empty deterministic and AI finding lists."""
    aggregator = ReviewAggregator()
    result = aggregator.aggregate([], [])

    assert isinstance(result, AggregatedReviewResult)
    assert result.score == 100.0
    assert result.grade == "A"
    assert len(result.findings) == 0
    assert result.total_deterministic == 0
    assert result.total_ai == 0
    assert result.total_deduplicated == 0
    assert result.severity_counts["critical"] == 0
    assert result.severity_counts["high"] == 0
    assert "Review Summary" in result.summary
    assert "No Issues Found" in result.summary


def test_severity_normalization() -> None:
    """Verify raw severity strings map correctly to standard severities."""
    aggregator = ReviewAggregator()

    raw_findings = [
        Finding(
            source="test",
            category="sec",
            severity="FATAL",
            title="Fatal Error",
            description="d1",
            file_path="a.py",
            line_number=1,
        ),
        Finding(
            source="test",
            category="sec",
            severity="MAJOR",
            title="Major Issue",
            description="d2",
            file_path="b.py",
            line_number=2,
        ),
        Finding(
            source="test",
            category="sec",
            severity="warn",
            title="Warning Issue",
            description="d3",
            file_path="c.py",
            line_number=3,
        ),
        Finding(
            source="test",
            category="sec",
            severity="style",
            title="Style Issue",
            description="d4",
            file_path="d.py",
            line_number=4,
        ),
        Finding(
            source="test",
            category="sec",
            severity="notice",
            title="Notice Issue",
            description="d5",
            file_path="e.py",
            line_number=5,
        ),
        Finding(
            source="test",
            category="sec",
            severity="UNRECOGNIZED_SEVERITY",
            title="Unknown Issue",
            description="d6",
            file_path="f.py",
            line_number=6,
        ),
    ]

    result = aggregator.aggregate(deterministic_findings=raw_findings)

    severities = [f.severity for f in result.findings]
    assert "critical" in severities
    assert "high" in severities
    assert "medium" in severities
    assert "low" in severities
    assert "info" in severities


def test_deduplication_exact_match() -> None:
    """Verify deterministic and AI findings on the same file and line get deduplicated."""
    aggregator = ReviewAggregator()

    deterministic = [
        Finding(
            source="rule_engine",
            category="security",
            severity="high",
            title="SQL Injection Risk",
            description="Rule engine detected dynamic SQL string query.",
            suggestion="Use parameterized queries.",
            file_path="app/db/query.py",
            line_number=42,
        )
    ]

    ai_findings = [
        Finding(
            source="ai:security",
            category="security",
            severity="critical",
            title="SQL Injection Vulnerability",
            description="AI reviewer flagged unescaped input in raw SQL query string.",
            suggestion="Use SQLAlchemy text() with bind parameters.",
            file_path="app/db/query.py",
            line_number=42,
        )
    ]

    result = aggregator.aggregate(
        deterministic_findings=deterministic, ai_findings=ai_findings
    )

    assert result.total_deterministic == 1
    assert result.total_ai == 1
    assert result.total_deduplicated == 1
    assert len(result.findings) == 1

    merged = result.findings[0]
    # Highest severity (critical > high) should be promoted
    assert merged.severity == "critical"
    # Sources should be merged alphabetically
    assert "ai:security" in merged.source
    assert "rule_engine" in merged.source
    assert merged.file_path == "app/db/query.py"
    assert merged.line_number == 42
    # Distinct descriptions should be merged
    assert "Rule engine detected" in merged.description
    assert "AI reviewer flagged" in merged.description
    # Suggestions should be merged
    assert "Use parameterized queries" in merged.suggestion
    assert "Use SQLAlchemy text()" in merged.suggestion


def test_deduplication_fuzzy_line_and_title_match() -> None:
    """Verify findings within 3 lines on the same file with identical title are deduplicated."""
    aggregator = ReviewAggregator()

    f1 = Finding(
        source="ai:clean_code",
        category="maintainability",
        severity="medium",
        title="Unused Variable",
        description="Variable `temp` is declared but never read.",
        file_path="app/services/user.py",
        line_number=10,
    )

    f2 = Finding(
        source="ai:architecture",
        category="maintainability",
        severity="low",
        title="Unused Variable",
        description="Variable `temp` is assigned but not used.",
        file_path="app/services/user.py",
        line_number=12,
    )

    result = aggregator.aggregate(ai_findings=[f1, f2])

    assert len(result.findings) == 1
    merged = result.findings[0]
    assert merged.severity == "medium"
    assert merged.file_path == "app/services/user.py"
    assert merged.line_number == 10
    assert "ai:clean_code" in merged.source
    assert "ai:architecture" in merged.source


def test_ranking_order() -> None:
    """Verify findings are ranked primarily by severity (critical > high > medium > low > info), secondarily by file path and line number."""
    aggregator = ReviewAggregator()

    findings = [
        Finding(
            source="ai",
            category="perf",
            severity="low",
            title="Low Issue B",
            file_path="b.py",
            line_number=10,
            description="d",
        ),
        Finding(
            source="ai",
            category="sec",
            severity="critical",
            title="Critical Issue",
            file_path="z.py",
            line_number=1,
            description="d",
        ),
        Finding(
            source="ai",
            category="perf",
            severity="high",
            title="High Issue A",
            file_path="a.py",
            line_number=20,
            description="d",
        ),
        Finding(
            source="ai",
            category="perf",
            severity="low",
            title="Low Issue A",
            file_path="a.py",
            line_number=5,
            description="d",
        ),
        Finding(
            source="ai",
            category="info",
            severity="info",
            title="Info Note",
            file_path="a.py",
            line_number=1,
            description="d",
        ),
    ]

    result = aggregator.aggregate(ai_findings=findings)
    ranked = result.findings

    assert len(ranked) == 5
    assert ranked[0].severity == "critical"
    assert ranked[0].title == "Critical Issue"

    assert ranked[1].severity == "high"
    assert ranked[1].title == "High Issue A"

    # Low issue A (file a.py, line 5) should come before Low issue B (file b.py, line 10)
    assert ranked[2].severity == "low"
    assert ranked[2].file_path == "a.py"

    assert ranked[3].severity == "low"
    assert ranked[3].file_path == "b.py"

    assert ranked[4].severity == "info"


def test_score_calculation_and_grades() -> None:
    """Verify score penalty calculation and letter grade boundaries."""
    aggregator = ReviewAggregator()

    # 1. Score 100 - 10 (medium) = 90.0 -> Grade A
    r1 = aggregator.aggregate(
        ai_findings=[
            Finding(
                source="ai",
                category="c",
                severity="medium",
                title="t",
                description="d",
            )
        ]
    )
    assert r1.score == 90.0
    assert r1.grade == "A"

    # 2. Score 100 - 20 (high) = 80.0 -> Grade B
    r2 = aggregator.aggregate(
        ai_findings=[
            Finding(
                source="ai", category="c", severity="high", title="t", description="d"
            )
        ]
    )
    assert r2.score == 80.0
    assert r2.grade == "B"

    # 3. Score 100 - 40 (critical) = 60.0 -> Grade C
    r3 = aggregator.aggregate(
        ai_findings=[
            Finding(
                source="ai",
                category="c",
                severity="critical",
                title="t",
                description="d",
            )
        ]
    )
    assert r3.score == 60.0
    assert r3.grade == "C"

    # 4. Score 100 - (40 + 40 + 40) = 0.0 -> Grade F
    r4 = aggregator.aggregate(
        ai_findings=[
            Finding(
                source="ai",
                category="c",
                severity="critical",
                title="t1",
                description="d1",
                file_path="f1.py",
                line_number=1,
            ),
            Finding(
                source="ai",
                category="c",
                severity="critical",
                title="t2",
                description="d2",
                file_path="f2.py",
                line_number=2,
            ),
            Finding(
                source="ai",
                category="c",
                severity="critical",
                title="t3",
                description="d3",
                file_path="f3.py",
                line_number=3,
            ),
        ]
    )
    assert r4.score == 0.0
    assert r4.grade == "F"


def test_custom_penalties_injection() -> None:
    """Verify custom score calculator and penalties override defaults."""
    custom_penalties = {"critical": 50.0, "high": 25.0, "medium": 15.0, "low": 5.0, "info": 0.0}
    aggregator = ReviewAggregator(
        score_calculator=ScoreCalculator(), custom_penalties=custom_penalties
    )

    finding = Finding(
        source="ai", category="c", severity="critical", title="t", description="d"
    )
    result = aggregator.aggregate(ai_findings=[finding])

    assert result.score == 50.0
    assert result.grade == "C"


def test_summary_report_structure() -> None:
    """Verify markdown summary report contains essential headings, metrics, urgent action items, and tables."""
    aggregator = ReviewAggregator()

    findings = [
        Finding(
            source="ai:security",
            category="security",
            severity="critical",
            title="Remote Code Execution",
            description="Use of unsafe `eval()` on unsanitized HTTP parameter.",
            suggestion="Replace `eval()` with safe JSON parser.",
            file_path="app/api/webhook.py",
            line_number=55,
        ),
        Finding(
            source="rule_engine",
            category="testing",
            severity="medium",
            title="Missing Unit Test Coverage",
            description="New module `webhook.py` has no corresponding test file.",
            file_path="app/api/webhook.py",
            line_number=1,
        ),
    ]

    result = aggregator.aggregate(
        deterministic_findings=[findings[1]], ai_findings=[findings[0]]
    )

    summary = result.summary

    assert "AI CodeGuardian Review Summary" in summary
    assert "**Overall Quality Score:**" in summary
    assert "### 📊 Review Overview" in summary
    assert "### 🚨 Urgent Action Required" in summary
    assert "Remote Code Execution" in summary
    assert "`app/api/webhook.py:55`" in summary
    assert "Replace `eval()` with safe JSON parser." in summary
    assert "### 📋 Ranked Findings" in summary
    assert "| `CRITICAL` | `security` |" in summary
    assert "| `MEDIUM` | `testing` |" in summary
