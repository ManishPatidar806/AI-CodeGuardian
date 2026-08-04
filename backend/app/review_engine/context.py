from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReviewContext:
    project_id: int
    mr_iid: int

    title: str
    description: str | None

    source_branch: str
    traget_branch: str
    commits: list[dict[str, Any]]
    diffs: list[dict[str, Any]]
