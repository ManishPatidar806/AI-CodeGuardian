from typing import Any
import httpx
import structlog
import base64
from urllib.parse import quote

from app.core.settings import settings

logger = structlog.get_logger(__name__)


class GitLabClient:
    def __init__(self) -> None:
        self.base_url = f"{settings.gitlab_url.rstrip('/')}/api/v4"

        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "PRIVATE-TOKEN": settings.gitlab_access_token,
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        try:
            response = self.client.get(path, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "gitlab_http_error",
                status_code=exc.response.status_code,
                path=path,
            )
            raise

        except httpx.RequestError:
            logger.exception(
                "gitlab_request_failed",
                path=path,
            )
            raise

    def get_project(self, project_id: int) -> dict[str, Any]:
        return self._get(f"/projects/{project_id}")

    def get_merge_request(
        self,
        project_id: int,
        mr_iid: int,
    ) -> dict[str, Any]:
        return self._get(f"/projects/{project_id}/merge_requests/{mr_iid}")

    def get_merge_request_commits(
        self,
        project_id: int,
        mr_iid: int,
    ) -> list[dict[str, Any]]:
        return self._get(f"/projects/{project_id}/merge_requests/{mr_iid}/commits")

    def get_merge_request_diffs(
        self,
        project_id: int,
        mr_iid: int,
    ) -> list[dict[str, Any]]:
        return self._get(
            f"/projects/{project_id}/merge_requests/{mr_iid}/diffs",
            params={
                "per_page": 100,
            },
        )

    def _get_all_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        page = 1

        while True:
            request_params = dict(params or {})
            request_params["page"] = page

            response = self.client.get(
                path,
                params=request_params,
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list):
                raise ValueError(f"Expected list response from GitLab: {path}")

            results.extend(data)

            next_page = response.headers.get("x-next-page")

            if not next_page:
                break

            page = int(next_page)

        return results

    def get_file_content(
        self,
        project_id: int,
        file_path: str,
        ref: str,
    ) -> str:
        encoded_path = quote(
            file_path,
            safe="",
        )

        data = self._get(
            f"/projects/{project_id}/repository/files/{encoded_path}",
            params={
                "ref": ref,
            },
        )

        content = data.get("content")

        if not content:
            return ""

        encoding = data.get("encoding")

        if encoding != "base64":
            raise ValueError(f"Unsupported GitLab file encoding: {encoding}")

        decoded = base64.b64decode(content)

        return decoded.decode(
            "utf-8",
            errors="replace",
        )

    def get_repository_tree(
        self,
        project_id: int,
        ref: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "recursive": True,
            "per_page": 100,
        }

        if ref:
            params["ref"] = ref

        return self._get_all_pages(
            f"/projects/{project_id}/repository/tree",
            params=params,
        )

    def get_merge_request_discussions(
        self,
        project_id: int,
        mr_iid: int,
    ) -> list[dict[str, Any]]:
        return self._get_all_pages(
            f"/projects/{project_id}/merge_requests/{mr_iid}/discussions"
        )

    def get_merge_request_versions(
        self,
        project_id: int,
        mr_iid: int,
    ) -> list[dict[str, Any]]:
        return self._get(f"/projects/{project_id}/merge_requests/{mr_iid}/versions")

    def post_merge_request_discussion(
        self,
        project_id: int,
        mr_iid: int,
        body: str,
        position: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"body": body}
        if position:
            payload["position"] = position

        try:
            response = self.client.post(
                f"/projects/{project_id}/merge_requests/{mr_iid}/discussions",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "gitlab_post_discussion_failed",
                status_code=exc.response.status_code,
                project_id=project_id,
                mr_iid=mr_iid,
            )
            raise

    def get_merge_request_approvals(
        self,
        project_id: int,
        mr_iid: int,
    ) -> dict[str, Any]:
        return self._get(f"/projects/{project_id}/merge_requests/{mr_iid}/approvals")

    def accept_merge_request(
        self,
        project_id: int,
        mr_iid: int,
        merge_commit_message: str | None = None,
        should_remove_source_branch: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "should_remove_source_branch": should_remove_source_branch,
        }
        if merge_commit_message:
            payload["merge_commit_message"] = merge_commit_message

        try:
            response = self.client.put(
                f"/projects/{project_id}/merge_requests/{mr_iid}/merge",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "gitlab_accept_merge_request_failed",
                status_code=exc.response.status_code,
                project_id=project_id,
                mr_iid=mr_iid,
            )
            raise

    def close(self) -> None:
        self.client.close()
