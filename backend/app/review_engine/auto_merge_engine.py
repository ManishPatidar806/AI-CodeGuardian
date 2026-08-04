from dataclasses import dataclass, field
from typing import Any

import structlog

from app.integrations.gitlab.client import GitLabClient

logger = structlog.get_logger(__name__)


@dataclass
class AutoMergeEvaluation:
    """Detailed evaluation report for all 6 auto-merge safety criteria.

    Attributes:
        can_merge: True if all 6 criteria are satisfied.
        all_reviewers_passed: True if no AI reviewer errors occurred.
        score_passed: True if review score >= min_auto_merge_score.
        ci_passed: True if GitLab CI pipeline succeeded.
        pipeline_successful: True if detailed pipeline status is mergeable.
        mr_approved: True if Merge Request is approved by human reviewers.
        no_unresolved_discussions: True if all discussion threads are resolved.
        score: Actual review score evaluated.
        min_score_threshold: Required score threshold.
        rejection_reasons: List of explicit reasons if merge is declined.
    """

    can_merge: bool
    all_reviewers_passed: bool
    score_passed: bool
    ci_passed: bool
    pipeline_successful: bool
    mr_approved: bool
    no_unresolved_discussions: bool
    score: float
    min_score_threshold: float
    rejection_reasons: list[str] = field(default_factory=list)


@dataclass
class AutoMergeResult:
    """Final result produced by AutoMergeEngine.

    Attributes:
        evaluation: Detailed AutoMergeEvaluation report.
        merged: True if merge request was successfully accepted.
        merge_commit_sha: Commit SHA returned by GitLab upon successful merge.
        message: Human-readable status message.
    """

    evaluation: AutoMergeEvaluation
    merged: bool
    merge_commit_sha: str | None = None
    message: str = ""


class AutoMergeEngine:
    """Evaluates strict multi-gate criteria and automatically merges GitLab Merge Requests.

    The AutoMergeEngine forms Phase 7 of the AI CodeGuardian pipeline.
    It automatically accepts merge requests ONLY when all 6 safety criteria pass:
    1. All AI reviewers executed successfully (no reviewer errors)
    2. Review score >= configured threshold (default 80.0)
    3. GitLab CI pipeline state is 'success' or 'passed'
    4. Detailed pipeline status is mergeable (no pending/failed jobs)
    5. Merge Request is approved by human reviewers
    6. All inline discussion threads are resolved
    """

    def __init__(
        self,
        gitlab_client: GitLabClient,
        min_auto_merge_score: float = 80.0,
        require_approval: bool = True,
        remove_source_branch: bool = True,
    ) -> None:
        """Initialize AutoMergeEngine.

        Args:
            gitlab_client: GitLabClient instance for REST API integration.
            min_auto_merge_score: Minimum quality score required for auto-merge.
            require_approval: True if MR must have human approval before auto-merging.
            remove_source_branch: True to delete feature branch upon successful merge.
        """
        self.gitlab_client = gitlab_client
        self.min_auto_merge_score = min_auto_merge_score
        self.require_approval = require_approval
        self.remove_source_branch = remove_source_branch

    def evaluate_and_merge(
        self,
        project_id: int,
        mr_iid: int,
        review_score: float,
        reviewer_errors: dict[str, str] | None = None,
        custom_commit_message: str | None = None,
    ) -> AutoMergeResult:
        """Evaluate all 6 auto-merge criteria and merge the MR if compliant.

        Args:
            project_id: GitLab project ID or path_with_namespace.
            mr_iid: Merge Request internal ID (IID).
            review_score: Overall calculated quality score (0.0 to 100.0).
            reviewer_errors: Optional dict of reviewer errors from ReviewCoordinator.
            custom_commit_message: Optional custom merge commit message.

        Returns:
            AutoMergeResult object detailing evaluation status and merge outcome.
        """
        logger.info(
            "auto_merge_evaluation_started",
            project_id=project_id,
            mr_iid=mr_iid,
            review_score=review_score,
            has_errors=bool(reviewer_errors),
        )

        rejection_reasons: list[str] = []

        # 1. Check AI Reviewer Execution Status
        all_reviewers_passed = not bool(reviewer_errors)
        if not all_reviewers_passed:
            err_list = ", ".join(f"{k}: {v}" for k, v in (reviewer_errors or {}).items())
            rejection_reasons.append(f"AI Reviewer errors encountered: [{err_list}]")

        # 2. Check Score Threshold
        score_passed = review_score >= self.min_auto_merge_score
        if not score_passed:
            rejection_reasons.append(
                f"Review score ({review_score:.1f}) is below threshold ({self.min_auto_merge_score:.1f})"
            )

        # 3. Fetch MR Details & Approvals from GitLab
        mr_data = self._fetch_mr_data(project_id, mr_iid)
        approvals_data = self._fetch_approvals_data(project_id, mr_iid)
        discussions_data = self._fetch_discussions_data(project_id, mr_iid)

        # 4. Check CI Pipeline Status
        ci_passed = self._evaluate_ci_passed(mr_data)
        if not ci_passed:
            rejection_reasons.append(
                f"CI pipeline status is not successful (state: '{self._get_ci_status(mr_data)}')"
            )

        # 5. Check Detailed Pipeline / Merge Status
        pipeline_successful = self._evaluate_pipeline_successful(mr_data)
        if not pipeline_successful:
            merge_status = mr_data.get("detailed_merge_status") or mr_data.get(
                "merge_status", "unknown"
            )
            rejection_reasons.append(
                f"Pipeline/Merge status is not ready (detailed_merge_status: '{merge_status}')"
            )

        # 6. Check MR Approval Status
        mr_approved = self._evaluate_mr_approved(mr_data, approvals_data)
        if self.require_approval and not mr_approved:
            rejection_reasons.append("Merge Request is not approved by human reviewers")

        # 7. Check Unresolved Discussions
        no_unresolved_discussions = self._evaluate_discussions_resolved(
            mr_data, discussions_data
        )
        if not no_unresolved_discussions:
            rejection_reasons.append("Merge Request has unresolved code discussion threads")

        # Combine evaluation status
        can_merge = (
            all_reviewers_passed
            and score_passed
            and ci_passed
            and pipeline_successful
            and (mr_approved or not self.require_approval)
            and no_unresolved_discussions
        )

        evaluation = AutoMergeEvaluation(
            can_merge=can_merge,
            all_reviewers_passed=all_reviewers_passed,
            score_passed=score_passed,
            ci_passed=ci_passed,
            pipeline_successful=pipeline_successful,
            mr_approved=mr_approved,
            no_unresolved_discussions=no_unresolved_discussions,
            score=review_score,
            min_score_threshold=self.min_auto_merge_score,
            rejection_reasons=rejection_reasons,
        )

        if not can_merge:
            logger.info(
                "auto_merge_declined",
                project_id=project_id,
                mr_iid=mr_iid,
                reasons=rejection_reasons,
            )
            return AutoMergeResult(
                evaluation=evaluation,
                merged=False,
                message=f"Auto-merge declined due to: {'; '.join(rejection_reasons)}",
            )

        # Execute Auto-Merge via GitLab REST API
        commit_msg = (
            custom_commit_message
            or f"AI CodeGuardian Auto-Merge (Score: {review_score:.1f}/100.0)"
        )

        try:
            merge_response = self.gitlab_client.accept_merge_request(
                project_id=project_id,
                mr_iid=mr_iid,
                merge_commit_message=commit_msg,
                should_remove_source_branch=self.remove_source_branch,
            )
            commit_sha = str(merge_response.get("merge_commit_sha", ""))

            logger.info(
                "auto_merge_executed_successfully",
                project_id=project_id,
                mr_iid=mr_iid,
                merge_commit_sha=commit_sha,
            )

            return AutoMergeResult(
                evaluation=evaluation,
                merged=True,
                merge_commit_sha=commit_sha,
                message="Merge Request automatically merged successfully",
            )

        except Exception as exc:
            err_msg = f"GitLab accept_merge_request API call failed: {str(exc)}"
            logger.error(
                "auto_merge_api_execution_failed",
                project_id=project_id,
                mr_iid=mr_iid,
                error=err_msg,
            )
            evaluation.rejection_reasons.append(err_msg)
            return AutoMergeResult(
                evaluation=evaluation,
                merged=False,
                message=err_msg,
            )

    def _fetch_mr_data(self, project_id: int, mr_iid: int) -> dict[str, Any]:
        try:
            return self.gitlab_client.get_merge_request(project_id, mr_iid)
        except Exception as e:
            logger.warning("failed_to_fetch_mr", error=str(e))
            return {}

    def _fetch_approvals_data(self, project_id: int, mr_iid: int) -> dict[str, Any]:
        try:
            return self.gitlab_client.get_merge_request_approvals(project_id, mr_iid)
        except Exception as e:
            logger.warning("failed_to_fetch_approvals", error=str(e))
            return {}

    def _fetch_discussions_data(
        self, project_id: int, mr_iid: int
    ) -> list[dict[str, Any]]:
        try:
            return self.gitlab_client.get_merge_request_discussions(project_id, mr_iid)
        except Exception as e:
            logger.warning("failed_to_fetch_discussions", error=str(e))
            return []

    def _get_ci_status(self, mr_data: dict[str, Any]) -> str:
        pipeline = mr_data.get("pipeline") or mr_data.get("head_pipeline") or {}
        if isinstance(pipeline, dict):
            return str(pipeline.get("status", "none")).lower()
        return "none"

    def _evaluate_ci_passed(self, mr_data: dict[str, Any]) -> bool:
        status = self._get_ci_status(mr_data)
        return status in ("success", "passed")

    def _evaluate_pipeline_successful(self, mr_data: dict[str, Any]) -> bool:
        detailed_status = str(
            mr_data.get("detailed_merge_status")
            or mr_data.get("merge_status", "")
        ).lower()

        if detailed_status in ("ci_must_pass", "ci_still_running", "cannot_be_merged", "checking"):
            return False

        has_conflicts = bool(mr_data.get("has_conflicts", False))
        return not has_conflicts

    def _evaluate_mr_approved(
        self,
        mr_data: dict[str, Any],
        approvals_data: dict[str, Any],
    ) -> bool:
        if mr_data.get("upvotes", 0) > 0:
            return True
        if mr_data.get("user_has_approved", False):
            return True

        approved = approvals_data.get("approved")
        if approved is True:
            return True

        approved_by = approvals_data.get("approved_by") or []
        if isinstance(approved_by, list) and len(approved_by) > 0:
            return True

        approvals_left = approvals_data.get("approvals_left")
        if approvals_left is not None and int(approvals_left) == 0:
            return True

        return False

    def _evaluate_discussions_resolved(
        self,
        mr_data: dict[str, Any],
        discussions_data: list[dict[str, Any]],
    ) -> bool:
        # Check GitLab MR flag if present
        if "blocking_discussions_resolved" in mr_data:
            return bool(mr_data["blocking_discussions_resolved"])

        # Manually inspect discussions
        for discussion in discussions_data or []:
            notes = discussion.get("notes") or []
            for note in notes:
                if note.get("resolvable") is True and note.get("resolved") is False:
                    return False

        return True
