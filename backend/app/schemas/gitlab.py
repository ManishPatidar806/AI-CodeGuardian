from pydantic import BaseModel, ConfigDict


class GitLabProject(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    path_with_namespace: str
    default_branch: str


class GitLabUser(BaseModel):
    model_config = ConfigDict(extra="ignore")

    username: str


class GitLabCommit(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str


class GitLabMergeRequestAttributes(BaseModel):
    model_config = ConfigDict(extra="ignore")

    iid: int
    title: str
    description: str | None = None

    source_branch: str
    target_branch: str

    state: str
    url: str | None = None

    last_commit: GitLabCommit | None = None


class GitLabMergeRequestEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    object_kind: str

    project: GitLabProject
    user: GitLabUser
    object_attributes: GitLabMergeRequestAttributes


class GitLabWebhookResponse(BaseModel):
    status: str
    message: str
    merge_request_id: int | None = None
