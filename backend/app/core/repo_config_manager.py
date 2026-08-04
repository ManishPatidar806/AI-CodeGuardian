from pydantic import BaseModel, Field
import structlog

from app.cache.guardian_cache import CodeGuardianCache
from app.core.config_manager import GuardianConfig, config_manager

logger = structlog.get_logger(__name__)


class RepoConfigOverride(BaseModel):
    """Pydantic model representing per-repository configuration overrides.

    Attributes:
        repository_id: Foreign key ID of Repository.
        review_score_threshold: Optional override for review score threshold.
        auto_merge_score_threshold: Optional override for auto-merge score threshold.
        llm_model: Optional override for AI model.
        rules_enabled: Optional override for rule category toggles.
    """

    repository_id: int
    review_score_threshold: float | None = Field(default=None, ge=0.0, le=100.0)
    auto_merge_score_threshold: float | None = Field(default=None, ge=0.0, le=100.0)
    llm_model: str | None = Field(default=None)
    rules_enabled: dict[str, bool] | None = Field(default=None)


class RepoConfigurationManager:
    """Service for managing per-repository configuration overrides and hierarchical merging."""

    CACHE_NAMESPACE = "config_repo"

    def __init__(self, cache: CodeGuardianCache | None = None) -> None:
        """Initialize RepoConfigurationManager.

        Args:
            cache: Optional CodeGuardianCache instance.
        """
        self.cache = cache or CodeGuardianCache()
        self._memory_overrides: dict[int, RepoConfigOverride] = {}

    def get_repo_override(self, repository_id: int) -> RepoConfigOverride | None:
        """Retrieve stored configuration override for a specific repository.

        Args:
            repository_id: Foreign key ID of Repository.

        Returns:
            RepoConfigOverride instance if present, else None.
        """
        cached_dict = self.cache.cache_service.get(self.CACHE_NAMESPACE, str(repository_id))
        if isinstance(cached_dict, dict):
            try:
                return RepoConfigOverride(**cached_dict)
            except Exception as exc:
                logger.warning("invalid_cached_repo_config", repo_id=repository_id, error=str(exc))

        return self._memory_overrides.get(repository_id)

    def set_repo_override(
        self, repository_id: int, override: RepoConfigOverride
    ) -> RepoConfigOverride:
        """Set and persist per-repository configuration override.

        Args:
            repository_id: Foreign key ID of Repository.
            override: Validated RepoConfigOverride instance.

        Returns:
            Saved RepoConfigOverride instance.
        """
        self._memory_overrides[repository_id] = override
        self.cache.cache_service.set(
            namespace=self.CACHE_NAMESPACE,
            key=str(repository_id),
            value=override.model_dump(),
            ttl_seconds=None,
        )
        logger.info("repo_configuration_override_updated", repository_id=repository_id)
        return override

    def get_effective_config(self, repository_id: int) -> GuardianConfig:
        """Compute effective runtime configuration by merging global config with repo overrides.

        Args:
            repository_id: Foreign key ID of Repository.

        Returns:
            GuardianConfig instance with repository overrides applied.
        """
        global_cfg = config_manager.get_config()
        override = self.get_repo_override(repository_id)

        if not override:
            return global_cfg

        merged_dict = global_cfg.model_dump()

        if override.review_score_threshold is not None:
            merged_dict["review_score_threshold"] = override.review_score_threshold
        if override.auto_merge_score_threshold is not None:
            merged_dict["auto_merge_score_threshold"] = override.auto_merge_score_threshold
        if override.llm_model is not None:
            merged_dict["llm_model"] = override.llm_model
        if override.rules_enabled is not None:
            merged_dict["rules_enabled"] = {
                **global_cfg.rules_enabled,
                **override.rules_enabled,
            }

        return GuardianConfig(**merged_dict)


# Global Repo Configuration Manager Instance
repo_config_manager = RepoConfigurationManager()
