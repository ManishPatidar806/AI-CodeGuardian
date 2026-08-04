from unittest.mock import MagicMock

from app.integrations.gitlab.client import GitLabClient
from app.review_engine.finding import Finding
from app.review_engine.inline_comment_engine import (
    GitLabDiffPosition,
    InlineCommentEngine,
    InlineCommentReport,
)


def create_mock_gitlab_client() -> MagicMock:
    """Helper factory to create a mock GitLabClient."""
    client = MagicMock(spec=GitLabClient)
    client.get_merge_request_versions.return_value = [
        {
            "base_commit_sha": "sha_base_123",
            "start_commit_sha": "sha_start_123",
            "head_commit_sha": "sha_head_123",
        }
    ]
    client.get_merge_request_diffs.return_value = [
        {
            "new_path": "app/services/user.py",
            "old_path": "app/services/user.py",
            "diff": "@@ -1,5 +1,6 @@\n import os\n+class SecurityReviewer:\n+    pass\n",
        }
    ]
    client.get_merge_request_discussions.return_value = []
    client.post_merge_request_discussion.return_value = {"id": "disc_999"}
    return client


def test_post_inline_comments_success() -> None:
    """Verify inline comments are posted with position object for lines inside MR diff."""
    mock_client = create_mock_gitlab_client()
    engine = InlineCommentEngine(gitlab_client=mock_client)

    finding = Finding(
        source="ai:security",
        category="security",
        severity="critical",
        title="Hardcoded Password",
        description="Found hardcoded secret in user service.",
        suggestion="Use environment variables.",
        file_path="app/services/user.py",
        line_number=2,
    )

    report = engine.post_inline_comments(
        project_id=10, mr_iid=5, findings=[finding]
    )

    assert isinstance(report, InlineCommentReport)
    assert report.total_findings == 1
    assert report.comments_posted == 1
    assert report.duplicates_skipped == 0
    assert report.failed_comments == 0
    assert "disc_999" in report.posted_discussion_ids

    mock_client.post_merge_request_discussion.assert_called_once()
    kwargs = mock_client.post_merge_request_discussion.call_args.kwargs
    assert kwargs["project_id"] == 10
    assert kwargs["mr_iid"] == 5
    assert "Hardcoded Password" in kwargs["body"]
    assert kwargs["position"]["new_line"] == 2
    assert kwargs["position"]["head_sha"] == "sha_head_123"


def test_duplicate_comments_filtered() -> None:
    """Verify existing MR discussions with matching title/fingerprint are skipped."""
    mock_client = create_mock_gitlab_client()
    mock_client.get_merge_request_discussions.return_value = [
        {
            "id": "existing_disc_1",
            "notes": [
                {
                    "body": "### 🚨 AI CodeGuardian: `SQL Injection Vulnerability`\nDetails..."
                }
            ],
        }
    ]

    engine = InlineCommentEngine(gitlab_client=mock_client)

    duplicate_finding = Finding(
        source="ai:security",
        category="security",
        severity="critical",
        title="SQL Injection Vulnerability",
        description="Duplicate finding already posted in earlier pipeline run.",
        file_path="app/db/query.py",
        line_number=42,
    )

    report = engine.post_inline_comments(
        project_id=10, mr_iid=5, findings=[duplicate_finding]
    )

    assert report.total_findings == 1
    assert report.duplicates_skipped == 1
    assert report.comments_posted == 0
    mock_client.post_merge_request_discussion.assert_not_called()


def test_general_mr_discussion_fallback() -> None:
    """Verify findings with line numbers outside MR diff hunks fallback to general MR discussions."""
    mock_client = create_mock_gitlab_client()
    engine = InlineCommentEngine(gitlab_client=mock_client)

    finding_outside_diff = Finding(
        source="rule_engine",
        category="architecture",
        severity="medium",
        title="Missing Documentation",
        description="Module lacks docstrings.",
        file_path="app/services/user.py",
        line_number=999,  # Line 999 is outside diff hunk
    )

    report = engine.post_inline_comments(
        project_id=10, mr_iid=5, findings=[finding_outside_diff]
    )

    assert report.total_findings == 1
    assert report.general_discussions_posted == 1
    assert report.comments_posted == 0

    mock_client.post_merge_request_discussion.assert_called_once()
    kwargs = mock_client.post_merge_request_discussion.call_args.kwargs
    assert kwargs["position"] is None


def test_diff_position_object_creation() -> None:
    """Verify GitLabDiffPosition serialization to dictionary."""
    pos = GitLabDiffPosition(
        base_sha="b123",
        start_sha="s123",
        head_sha="h123",
        new_path="a.py",
        old_path="a.py",
        new_line=15,
    )

    d = pos.to_dict()
    assert d["base_sha"] == "b123"
    assert d["start_sha"] == "s123"
    assert d["head_sha"] == "h123"
    assert d["position_type"] == "text"
    assert d["new_path"] == "a.py"
    assert d["new_line"] == 15


def test_format_comment_body() -> None:
    """Verify format_comment_body outputs structured Markdown with severity emoji and recommendation."""
    mock_client = create_mock_gitlab_client()
    engine = InlineCommentEngine(gitlab_client=mock_client)

    finding = Finding(
        source="ai:clean_code",
        category="clean_code",
        severity="high",
        title="Complex Function",
        description="Cyclomatic complexity exceeds threshold.",
        suggestion="Split function into helper modules.",
    )

    body = engine.format_comment_body(finding)

    assert "### ⚠️ AI CodeGuardian: `Complex Function`" in body
    assert "**Severity:** `HIGH`" in body
    assert "**Category:** `clean_code`" in body
    assert "Cyclomatic complexity exceeds threshold." in body
    assert "**Recommendation / Suggested Fix:**" in body
    assert "Split function into helper modules." in body


def test_empty_findings_list() -> None:
    """Verify empty findings list returns clean report without API calls."""
    mock_client = create_mock_gitlab_client()
    engine = InlineCommentEngine(gitlab_client=mock_client)

    report = engine.post_inline_comments(project_id=10, mr_iid=5, findings=[])

    assert report.total_findings == 0
    assert report.comments_posted == 0
    mock_client.post_merge_request_discussion.assert_not_called()
