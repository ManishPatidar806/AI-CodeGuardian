from unittest.mock import MagicMock

from app.integrations.gitlab.client import GitLabClient
from app.review_engine.auto_merge_engine import (
    AutoMergeEngine,
    AutoMergeResult,
)


def create_mock_gitlab_client(
    ci_status: str = "success",
    approved: bool = True,
    has_unresolved_threads: bool = False,
    detailed_merge_status: str = "mergeable",
) -> MagicMock:
    """Helper factory to create a mock GitLabClient configured for auto-merge tests."""
    client = MagicMock(spec=GitLabClient)
    client.get_merge_request.return_value = {
        "pipeline": {"status": ci_status},
        "detailed_merge_status": detailed_merge_status,
        "has_conflicts": False,
        "upvotes": 1 if approved else 0,
        "user_has_approved": approved,
        "blocking_discussions_resolved": not has_unresolved_threads,
    }
    client.get_merge_request_approvals.return_value = {
        "approved": approved,
        "approved_by": [{"user": {"username": "lead_dev"}}] if approved else [],
        "approvals_left": 0 if approved else 1,
    }
    client.get_merge_request_discussions.return_value = [
        {
            "notes": [
                {
                    "resolvable": True,
                    "resolved": not has_unresolved_threads,
                }
            ]
        }
    ]
    client.accept_merge_request.return_value = {
        "merge_commit_sha": "sha_merge_999999",
        "state": "merged",
    }
    return client


def test_auto_merge_success() -> None:
    """Verify successful auto-merge when all 6 safety criteria are satisfied."""
    client = create_mock_gitlab_client(ci_status="success", approved=True)
    engine = AutoMergeEngine(gitlab_client=client, min_auto_merge_score=80.0)

    result = engine.evaluate_and_merge(
        project_id=1,
        mr_iid=42,
        review_score=95.0,
        reviewer_errors=None,
    )

    assert isinstance(result, AutoMergeResult)
    assert result.merged is True
    assert result.merge_commit_sha == "sha_merge_999999"
    assert result.evaluation.can_merge is True
    assert result.evaluation.all_reviewers_passed is True
    assert result.evaluation.score_passed is True
    assert result.evaluation.ci_passed is True
    assert result.evaluation.pipeline_successful is True
    assert result.evaluation.mr_approved is True
    assert result.evaluation.no_unresolved_discussions is True
    assert len(result.evaluation.rejection_reasons) == 0

    client.accept_merge_request.assert_called_once_with(
        project_id=1,
        mr_iid=42,
        merge_commit_message="AI CodeGuardian Auto-Merge (Score: 95.0/100.0)",
        should_remove_source_branch=True,
    )


def test_rejection_when_reviewer_failed() -> None:
    """Verify auto-merge is declined if an AI reviewer model encountered an error."""
    client = create_mock_gitlab_client()
    engine = AutoMergeEngine(gitlab_client=client)

    errors = {"SecurityReviewer": "Rate limit exceeded"}
    result = engine.evaluate_and_merge(
        project_id=1,
        mr_iid=42,
        review_score=90.0,
        reviewer_errors=errors,
    )

    assert result.merged is False
    assert result.evaluation.can_merge is False
    assert result.evaluation.all_reviewers_passed is False
    assert any("AI Reviewer errors" in r for r in result.evaluation.rejection_reasons)
    client.accept_merge_request.assert_not_called()


def test_rejection_when_score_below_threshold() -> None:
    """Verify auto-merge is declined if review score is below configured threshold."""
    client = create_mock_gitlab_client()
    engine = AutoMergeEngine(gitlab_client=client, min_auto_merge_score=80.0)

    result = engine.evaluate_and_merge(
        project_id=1,
        mr_iid=42,
        review_score=75.0,  # Below 80.0 threshold
    )

    assert result.merged is False
    assert result.evaluation.score_passed is False
    assert any("below threshold" in r for r in result.evaluation.rejection_reasons)
    client.accept_merge_request.assert_not_called()


def test_rejection_when_ci_failed() -> None:
    """Verify auto-merge is declined if GitLab CI status is failed."""
    client = create_mock_gitlab_client(ci_status="failed")
    engine = AutoMergeEngine(gitlab_client=client)

    result = engine.evaluate_and_merge(
        project_id=1,
        mr_iid=42,
        review_score=90.0,
    )

    assert result.merged is False
    assert result.evaluation.ci_passed is False
    assert any("CI pipeline status" in r for r in result.evaluation.rejection_reasons)
    client.accept_merge_request.assert_not_called()


def test_rejection_when_mr_unapproved() -> None:
    """Verify auto-merge is declined if MR is not approved by human reviewers."""
    client = create_mock_gitlab_client(approved=False)
    engine = AutoMergeEngine(gitlab_client=client, require_approval=True)

    result = engine.evaluate_and_merge(
        project_id=1,
        mr_iid=42,
        review_score=90.0,
    )

    assert result.merged is False
    assert result.evaluation.mr_approved is False
    assert any("not approved" in r for r in result.evaluation.rejection_reasons)
    client.accept_merge_request.assert_not_called()


def test_rejection_when_unresolved_discussions() -> None:
    """Verify auto-merge is declined if MR has unresolved code discussion threads."""
    client = create_mock_gitlab_client(has_unresolved_threads=True)
    engine = AutoMergeEngine(gitlab_client=client)

    result = engine.evaluate_and_merge(
        project_id=1,
        mr_iid=42,
        review_score=90.0,
    )

    assert result.merged is False
    assert result.evaluation.no_unresolved_discussions is False
    assert any("unresolved code discussion" in r for r in result.evaluation.rejection_reasons)
    client.accept_merge_request.assert_not_called()


def test_custom_commit_message_and_options() -> None:
    """Verify custom merge commit message and source branch deletion options are passed to GitLab."""
    client = create_mock_gitlab_client()
    engine = AutoMergeEngine(
        gitlab_client=client,
        remove_source_branch=False,
    )

    result = engine.evaluate_and_merge(
        project_id=1,
        mr_iid=42,
        review_score=90.0,
        custom_commit_message="Custom Merge Commit Message v1.0",
    )

    assert result.merged is True
    client.accept_merge_request.assert_called_once_with(
        project_id=1,
        mr_iid=42,
        merge_commit_message="Custom Merge Commit Message v1.0",
        should_remove_source_branch=False,
    )
