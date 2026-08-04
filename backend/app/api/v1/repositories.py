from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.repo_config_manager import RepoConfigOverride, repo_config_manager
from app.db.session import get_db
from app.repositories.repository_repo import RepositoryRepository
from app.services.repo_indexing_manager import repo_indexing_manager

router = APIRouter(prefix="/repositories", tags=["Repositories"])


class RepositoryCreateRequest(BaseModel):
    """Pydantic model for repository registration requests."""

    name: str = Field(..., min_length=1, description="Repository display name")
    path_with_namespace: str = Field(..., description="Full path namespace, e.g. owner/repo")
    default_branch: str = Field(default="main", description="Default branch name")
    gitlab_project_id: int | None = Field(default=None, description="GitLab Project ID")


class RepositoryIndexRequest(BaseModel):
    """Pydantic model for triggering repository indexing."""

    branch: str = Field(default="main", description="Target git branch name")


@router.post("", summary="Register New Repository")
def register_repository(
    payload: RepositoryCreateRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Register a new repository in AI CodeGuardian.

    Args:
        payload: Repository registration payload.
        db: Active SQLAlchemy Session.

    Returns:
        Created repository details dictionary.
    """
    repo_repo = RepositoryRepository(db)
    existing = repo_repo.get_by_path(payload.path_with_namespace)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Repository '{payload.path_with_namespace}' is already registered.",
        )

    repo = repo_repo.create_or_update(
        gitlab_project_id=payload.gitlab_project_id or 0,
        name=payload.name,
        path_with_namespace=payload.path_with_namespace,
        default_branch=payload.default_branch,
    )

    effective_cfg = repo_config_manager.get_effective_config(repo.id)
    indexing_status = repo_indexing_manager.get_indexing_status(repo.id)

    return {
        "id": repo.id,
        "name": repo.name,
        "path_with_namespace": repo.path_with_namespace,
        "default_branch": repo.default_branch,
        "gitlab_project_id": repo.gitlab_project_id,
        "effective_score_threshold": effective_cfg.review_score_threshold,
        "indexing_status": indexing_status["status"],
    }


@router.get("", summary="List Registered Repositories")
def list_repositories(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List all registered repositories with status and effective thresholds."""
    repo_repo = RepositoryRepository(db)
    repos = repo_repo.list_all()

    result = []
    for repo in repos:
        effective_cfg = repo_config_manager.get_effective_config(repo.id)
        indexing = repo_indexing_manager.get_indexing_status(repo.id)
        result.append(
            {
                "id": repo.id,
                "name": repo.name,
                "path_with_namespace": repo.path_with_namespace,
                "default_branch": repo.default_branch,
                "gitlab_project_id": repo.gitlab_project_id,
                "effective_score_threshold": effective_cfg.review_score_threshold,
                "indexing_status": indexing["status"],
            }
        )

    return result


@router.get("/{repo_id}", summary="Get Repository Details")
def get_repository(repo_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Retrieve details for a specific repository by ID."""
    repo_repo = RepositoryRepository(db)
    repo = repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository #{repo_id} not found.")

    effective_cfg = repo_config_manager.get_effective_config(repo.id)
    indexing = repo_indexing_manager.get_indexing_status(repo.id)
    override = repo_config_manager.get_repo_override(repo.id)

    return {
        "id": repo.id,
        "name": repo.name,
        "path_with_namespace": repo.path_with_namespace,
        "default_branch": repo.default_branch,
        "gitlab_project_id": repo.gitlab_project_id,
        "effective_config": effective_cfg.model_dump(),
        "has_override": override is not None,
        "indexing_status": indexing,
    }


@router.put("/{repo_id}/config", summary="Update Per-Repository Configuration Override")
def update_repo_config(
    repo_id: int, override: RepoConfigOverride, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Update per-repository configuration overrides.

    Args:
        repo_id: Foreign key ID of Repository.
        override: Validated RepoConfigOverride instance.
        db: Active SQLAlchemy Session.

    Returns:
        Updated effective repository configuration.
    """
    repo_repo = RepositoryRepository(db)
    repo = repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository #{repo_id} not found.")

    override.repository_id = repo_id
    saved_override = repo_config_manager.set_repo_override(repo_id, override)
    effective_cfg = repo_config_manager.get_effective_config(repo_id)

    return {
        "repository_id": repo_id,
        "override": saved_override.model_dump(),
        "effective_config": effective_cfg.model_dump(),
    }


@router.post("/{repo_id}/index", summary="Trigger Background Repository Indexing")
def trigger_repo_indexing(
    repo_id: int, payload: RepositoryIndexRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Trigger vector indexing for a repository.

    Args:
        repo_id: Foreign key ID of Repository.
        payload: Indexing parameter request.
        db: Active SQLAlchemy Session.

    Returns:
        Indexing status payload.
    """
    repo_repo = RepositoryRepository(db)
    repo = repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository #{repo_id} not found.")

    return repo_indexing_manager.trigger_repository_indexing(repo_id, payload.branch)
