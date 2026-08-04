from pydantic import BaseModel, Field, field_validator
import structlog

from app.cache.guardian_cache import CodeGuardianCache

logger = structlog.get_logger(__name__)


class GuardianConfig(BaseModel):
    """Pydantic model representing runtime configuration for AI CodeGuardian.

    Attributes:
        review_score_threshold: Minimum score (0-100) to pass review.
        auto_merge_score_threshold: Minimum score (0-100) to trigger auto-merge.
        llm_model: AI model choice ('gemini-2.5-flash', 'gemini-2.5-pro', 'gpt-4o', etc.).
        rules_enabled: Mapping of rule categories to enabled boolean flags.
        token_budgets: Percentage allocations for P1-P4 prompt context tiers.
        slack_channel: Target Slack channel for review notifications.
        slack_notification_trigger: Trigger mode ('on_all_reviews', 'on_failures_only', 'on_critical_only').
    """

    review_score_threshold: float = Field(
        default=80.0, ge=0.0, le=100.0, description="Passing score threshold"
    )
    auto_merge_score_threshold: float = Field(
        default=85.0, ge=0.0, le=100.0, description="Auto-merge score threshold"
    )
    llm_model: str = Field(
        default="gemini-2.5-flash", description="Target AI LLM model"
    )
    rules_enabled: dict[str, bool] = Field(
        default_factory=lambda: {
            "security": True,
            "performance": True,
            "clean_code": True,
            "testing": True,
            "architecture": True,
        },
        description="Rule engine category toggle flags",
    )
    token_budgets: dict[str, int] = Field(
        default_factory=lambda: {
            "p1_git_diff_pct": 45,
            "p2_rag_pct": 25,
            "p3_dep_graph_pct": 20,
            "p4_summary_pct": 10,
        },
        description="Context budget percentage allocations",
    )
    slack_channel: str = Field(
        default="#code-reviews", description="Default Slack channel"
    )
    slack_notification_trigger: str = Field(
        default="on_all_reviews", description="Slack notification trigger mode"
    )

    @field_validator("token_budgets")
    @classmethod
    def validate_token_budgets_total(cls, v: dict[str, int]) -> dict[str, int]:
        """Ensure token budget percentages sum to 100%."""
        total = sum(v.values())
        if total != 100:
            raise ValueError(f"Context token budgets must sum to 100%, got {total}%")
        return v


class ConfigurationManager:
    """Thread-safe manager for reading and updating AI CodeGuardian runtime configuration."""

    CACHE_NAMESPACE = "config"
    CACHE_KEY = "runtime"

    def __init__(self, cache: CodeGuardianCache | None = None) -> None:
        """Initialize ConfigurationManager.

        Args:
            cache: Optional CodeGuardianCache instance.
        """
        self.cache = cache or CodeGuardianCache()
        self._memory_config: GuardianConfig = GuardianConfig()

    def get_config(self) -> GuardianConfig:
        """Retrieve current runtime configuration from Redis cache or memory fallback.

        Returns:
            Current GuardianConfig instance.
        """
        cached_dict = self.cache.cache_service.get(self.CACHE_NAMESPACE, self.CACHE_KEY)
        if isinstance(cached_dict, dict):
            try:
                return GuardianConfig(**cached_dict)
            except Exception as exc:
                logger.warning("invalid_cached_config_fallback", error=str(exc))

        return self._memory_config

    def update_config(self, new_config: GuardianConfig) -> GuardianConfig:
        """Update and persist new runtime configuration in Redis cache and memory.

        Args:
            new_config: Validated GuardianConfig instance.

        Returns:
            Updated GuardianConfig instance.
        """
        self._memory_config = new_config
        self.cache.cache_service.set(
            namespace=self.CACHE_NAMESPACE,
            key=self.CACHE_KEY,
            value=new_config.model_dump(),
            ttl_seconds=None,  # Permanent runtime config
        )
        logger.info("runtime_configuration_updated", llm_model=new_config.llm_model, pass_threshold=new_config.review_score_threshold)
        return new_config


# Global Configuration Manager Instance
config_manager = ConfigurationManager()
