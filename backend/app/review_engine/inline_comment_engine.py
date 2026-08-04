from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import re
from typing import Any, Sequence

import structlog

from app.integrations.gitlab.client import GitLabClient
from app.review_engine.finding import Finding

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class GitLabDiffPosition:
    """GitLab position object required for posting inline merge request comments.

    Attributes:
        base_sha: Base commit SHA.
        start_sha: Start commit SHA.
        head_sha: Head commit SHA of the merge request.
        new_path: Modified file path.
        old_path: Original file path.
        new_line: Line number in the new file diff.
        position_type: Type of position (always 'text' for code diffs).
    """

    base_sha: str
    start_sha: str
    head_sha: str
    new_path: str
    old_path: str
    new_line: int
    position_type: str = "text"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary payload for GitLab REST API."""
        return {
            "base_sha": self.base_sha,
            "start_sha": self.start_sha,
            "head_sha": self.head_sha,
            "position_type": self.position_type,
            "new_path": self.new_path,
            "old_path": self.old_path,
            "new_line": self.new_line,
        }


@dataclass
class InlineCommentReport:
    """Execution statistics report produced by InlineCommentEngine.

    Attributes:
        total_findings: Total number of input findings processed.
        comments_posted: Count of inline comments successfully posted.
        general_discussions_posted: Count of general MR discussions posted (line outside diff).
        duplicates_skipped: Count of findings skipped because duplicate comments already existed.
        failed_comments: Count of comment post failures.
        posted_discussion_ids: List of GitLab discussion IDs created.
    """

    total_findings: int = 0
    comments_posted: int = 0
    general_discussions_posted: int = 0
    duplicates_skipped: int = 0
    failed_comments: int = 0
    posted_discussion_ids: list[str] = field(default_factory=list)


class InlineCommentEngine:
    """Maps AI and deterministic findings to GitLab diff lines and posts inline review comments.

    The InlineCommentEngine forms Phase 5 of the AI CodeGuardian pipeline.
    It handles:
    - Diff position resolution (base_sha, start_sha, head_sha)
    - Validating line numbers against MR diff hunks
    - Deduplicating findings against existing GitLab MR discussions
    - Generating standardized Markdown review comments
    - Batching concurrent API requests to GitLab
    """

    def __init__(
        self,
        gitlab_client: GitLabClient,
        max_batch_workers: int = 5,
    ) -> None:
        """Initialize InlineCommentEngine.

        Args:
            gitlab_client: GitLabClient instance for REST API operations.
            max_batch_workers: Maximum concurrent workers for batching REST requests.
        """
        self.gitlab_client = gitlab_client
        self.max_batch_workers = max_batch_workers

    def post_inline_comments(
        self,
        project_id: int,
        mr_iid: int,
        findings: Sequence[Finding],
    ) -> InlineCommentReport:
        """Post inline review comments for the provided findings to the specified GitLab Merge Request.

        Args:
            project_id: GitLab project ID or path_with_namespace.
            mr_iid: Merge Request internal ID (IID).
            findings: Sequence of Finding objects to post.

        Returns:
            InlineCommentReport summarizing posted, skipped, and failed comments.
        """
        start_findings = list(findings or [])
        if not start_findings:
            logger.info("inline_comments_no_findings", project_id=project_id, mr_iid=mr_iid)
            return InlineCommentReport()

        logger.info(
            "inline_comment_processing_started",
            project_id=project_id,
            mr_iid=mr_iid,
            finding_count=len(start_findings),
        )

        # 1. Fetch MR version SHAs and diffs
        version_shas = self._fetch_version_shas(project_id, mr_iid)
        mr_diffs = self.gitlab_client.get_merge_request_diffs(project_id, mr_iid)
        valid_diff_lines = self._build_valid_diff_lines_map(mr_diffs)

        # 2. Fetch existing discussions to avoid duplicate comments
        existing_discussions = self.gitlab_client.get_merge_request_discussions(
            project_id, mr_iid
        )
        existing_fingerprints = self._extract_existing_fingerprints(existing_discussions)

        # 3. Filter findings and build comment tasks
        tasks_to_post: list[tuple[Finding, GitLabDiffPosition | None, str]] = []
        duplicates_skipped = 0

        for finding in start_findings:
            fingerprint = self._generate_finding_fingerprint(finding)
            if fingerprint in existing_fingerprints:
                logger.debug(
                    "duplicate_comment_skipped",
                    title=finding.title,
                    file_path=finding.file_path,
                    line_number=finding.line_number,
                )
                duplicates_skipped += 1
                continue

            # Determine position
            position = self._resolve_diff_position(
                finding=finding,
                version_shas=version_shas,
                valid_diff_lines=valid_diff_lines,
            )

            # Format comment body
            comment_body = self.format_comment_body(finding)
            tasks_to_post.append((finding, position, comment_body))

        # 4. Batch post comments concurrently using ThreadPoolExecutor
        report = InlineCommentReport(
            total_findings=len(start_findings),
            duplicates_skipped=duplicates_skipped,
        )

        if not tasks_to_post:
            logger.info("inline_comments_all_skipped", duplicates_skipped=duplicates_skipped)
            return report

        self._execute_batch_posting(
            project_id=project_id,
            mr_iid=mr_iid,
            tasks=tasks_to_post,
            report=report,
        )

        logger.info(
            "inline_comment_processing_completed",
            posted=report.comments_posted,
            general=report.general_discussions_posted,
            duplicates_skipped=report.duplicates_skipped,
            failed=report.failed_comments,
        )

        return report

    def format_comment_body(self, finding: Finding) -> str:
        """Format Finding object into a rich Markdown inline comment body.

        Args:
            finding: Input Finding object.

        Returns:
            Formatted Markdown string.
        """
        sev_upper = finding.severity.upper()
        severity_emoji = {
            "CRITICAL": "🚨",
            "HIGH": "⚠️",
            "MEDIUM": "🟡",
            "LOW": "🔹",
            "INFO": "ℹ️",
        }.get(sev_upper, "🔍")

        lines = [
            f"### {severity_emoji} AI CodeGuardian: `{finding.title}`",
            f"**Severity:** `{sev_upper}` | **Category:** `{finding.category}` | **Source:** `{finding.source}`",
            "",
            "**Description:**",
            finding.description,
        ]

        if finding.suggestion:
            lines.extend(
                [
                    "",
                    "**Recommendation / Suggested Fix:**",
                    finding.suggestion,
                ]
            )

        return "\n".join(lines)

    def _fetch_version_shas(
        self,
        project_id: int,
        mr_iid: int,
    ) -> dict[str, str]:
        """Fetch latest base_sha, start_sha, and head_sha for MR.

        Args:
            project_id: Project ID.
            mr_iid: MR IID.

        Returns:
            Dict containing 'base_sha', 'start_sha', 'head_sha'.
        """
        try:
            versions = self.gitlab_client.get_merge_request_versions(project_id, mr_iid)
            if versions and isinstance(versions, list):
                latest = versions[0]
                return {
                    "base_sha": str(latest.get("base_commit_sha", "")),
                    "start_sha": str(latest.get("start_commit_sha", "")),
                    "head_sha": str(latest.get("head_commit_sha", "")),
                }
        except Exception as e:
            logger.warning("failed_to_fetch_mr_versions", error=str(e))

        return {"base_sha": "", "start_sha": "", "head_sha": ""}

    def _build_valid_diff_lines_map(
        self,
        mr_diffs: list[dict[str, Any]],
    ) -> dict[str, set[int]]:
        """Parse MR diff hunks to construct a map of modified new_file line numbers.

        Args:
            mr_diffs: List of MR diff dictionaries.

        Returns:
            Dict mapping file_path to set of valid added/modified line numbers.
        """
        valid_lines: dict[str, set[int]] = {}

        for diff_file in mr_diffs or []:
            new_path = diff_file.get("new_path")
            diff_text = diff_file.get("diff")

            if not new_path or not diff_text:
                continue

            lines_set: set[int] = set()
            current_new_line = 0

            for line in diff_text.splitlines():
                if line.startswith("@@"):
                    # Parse diff hunk header @@ -old_start,old_count +new_start,new_count @@
                    match = re.search(r"\+(\d+)(?:,(\d+))?", line)
                    if match:
                        current_new_line = int(match.group(1))
                elif line.startswith("+") and not line.startswith("+++"):
                    lines_set.add(current_new_line)
                    current_new_line += 1
                elif not line.startswith("-"):
                    current_new_line += 1

            valid_lines[new_path] = lines_set

        return valid_lines

    def _resolve_diff_position(
        self,
        finding: Finding,
        version_shas: dict[str, str],
        valid_diff_lines: dict[str, set[int]],
    ) -> GitLabDiffPosition | None:
        """Resolve GitLabDiffPosition if finding line falls within MR diff hunks.

        Args:
            finding: Finding object.
            version_shas: Dict with SHAs.
            valid_diff_lines: Map of file_path to set of valid modified lines.

        Returns:
            GitLabDiffPosition if line is in diff, None otherwise.
        """
        if not finding.file_path or finding.line_number is None:
            return None

        file_path = finding.file_path.strip()
        line_num = finding.line_number

        valid_lines = valid_diff_lines.get(file_path, set())
        if line_num not in valid_lines:
            logger.debug(
                "line_outside_mr_diff_hunk",
                file_path=file_path,
                line_number=line_num,
            )
            return None

        if not version_shas.get("head_sha"):
            return None

        return GitLabDiffPosition(
            base_sha=version_shas["base_sha"],
            start_sha=version_shas["start_sha"],
            head_sha=version_shas["head_sha"],
            new_path=file_path,
            old_path=file_path,
            new_line=line_num,
        )

    def _extract_existing_fingerprints(
        self,
        discussions: list[dict[str, Any]],
    ) -> set[str]:
        """Extract unique finding fingerprints from existing GitLab MR discussions.

        Args:
            discussions: List of discussion dicts.

        Returns:
            Set of existing fingerprint strings.
        """
        fingerprints: set[str] = set()

        for discussion in discussions or []:
            notes = discussion.get("notes") or []
            for note in notes:
                body = str(note.get("body") or "")
                # Extract title header if posted by AI CodeGuardian
                match = re.search(r"### .* AI CodeGuardian: `([^`]+)`", body)
                if match:
                    title = match.group(1).strip().lower()
                    fingerprints.add(title)
                elif "AI CodeGuardian" in body:
                    # Generic body fingerprinting
                    fingerprints.add(body[:100].strip().lower())

        return fingerprints

    def _generate_finding_fingerprint(self, finding: Finding) -> str:
        """Generate deduplication fingerprint for finding.

        Args:
            finding: Finding object.

        Returns:
            Fingerprint string.
        """
        return finding.title.strip().lower()

    def _execute_batch_posting(
        self,
        project_id: int,
        mr_iid: int,
        tasks: list[tuple[Finding, GitLabDiffPosition | None, str]],
        report: InlineCommentReport,
    ) -> None:
        """Post comments concurrently using a thread pool.

        Args:
            project_id: GitLab project ID.
            mr_iid: Merge Request IID.
            tasks: List of (finding, position, comment_body) tuples.
            report: InlineCommentReport to update.
        """
        with ThreadPoolExecutor(max_workers=self.max_batch_workers) as executor:
            future_to_task = {
                executor.submit(
                    self._post_single_comment,
                    project_id=project_id,
                    mr_iid=mr_iid,
                    position=pos,
                    body=body,
                ): (finding, pos)
                for finding, pos, body in tasks
            }

            for future in as_completed(future_to_task):
                finding, pos = future_to_task[future]
                try:
                    res = future.result()
                    disc_id = str(res.get("id", ""))
                    if disc_id:
                        report.posted_discussion_ids.append(disc_id)

                    if pos is not None:
                        report.comments_posted += 1
                    else:
                        report.general_discussions_posted += 1
                except Exception as exc:
                    logger.error(
                        "failed_to_post_inline_comment",
                        title=finding.title,
                        file_path=finding.file_path,
                        error=str(exc),
                    )
                    report.failed_comments += 1

    def _post_single_comment(
        self,
        project_id: int,
        mr_iid: int,
        position: GitLabDiffPosition | None,
        body: str,
    ) -> dict[str, Any]:
        """Internal helper to post a single comment to GitLab.

        Args:
            project_id: Project ID.
            mr_iid: MR IID.
            position: Position object or None.
            body: Comment markdown text.

        Returns:
            Response dict from GitLab REST API.
        """
        pos_dict = position.to_dict() if position else None
        return self.gitlab_client.post_merge_request_discussion(
            project_id=project_id,
            mr_iid=mr_iid,
            body=body,
            position=pos_dict,
        )
