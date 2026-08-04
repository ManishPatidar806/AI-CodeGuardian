from typing import ClassVar
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
import structlog

logger = structlog.get_logger(__name__)


class PrometheusMetricsService:
    """Production Prometheus metrics service for AI CodeGuardian.

    Tracks:
    1. Reviews processed (total reviews by status)
    2. Rule engine findings (by category and severity)
    3. AI review latencies (histogram by reviewer_name)
    4. Tokens consumed (by token_type and model_name)
    5. Cost metrics (estimated USD cost by model_name)
    6. Merge rate (auto-merge evaluation status)
    7. Failed reviews (failure count by error_type)
    """

    _instance: ClassVar["PrometheusMetricsService | None"] = None

    def __new__(cls) -> "PrometheusMetricsService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_metrics()
        return cls._instance

    def _initialize_metrics(self) -> None:
        """Initialize Prometheus Registry and metric instruments."""
        self.registry = CollectorRegistry(auto_describe=True)

        # 1. Reviews processed
        self.REVIEWS_PROCESSED = Counter(
            "codeguardian_reviews_processed_total",
            "Total number of code reviews processed by AI CodeGuardian",
            ["status"],
            registry=self.registry,
        )

        # 2. Rule engine findings
        self.RULE_FINDINGS = Counter(
            "codeguardian_rule_engine_findings_total",
            "Total number of rule engine findings generated",
            ["category", "severity"],
            registry=self.registry,
        )

        # 3. AI review latencies
        self.REVIEW_LATENCY = Histogram(
            "codeguardian_ai_review_latency_seconds",
            "AI review execution latency in seconds",
            ["reviewer_name"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
            registry=self.registry,
        )

        # 4. Tokens consumed
        self.TOKENS_CONSUMED = Counter(
            "codeguardian_llm_tokens_consumed_total",
            "Total LLM tokens consumed",
            ["token_type", "model_name"],
            registry=self.registry,
        )

        # 5. Cost metrics
        self.LLM_COST = Counter(
            "codeguardian_llm_cost_usd_total",
            "Total estimated LLM consumption cost in USD",
            ["model_name"],
            registry=self.registry,
        )

        # 6. Merge rate
        self.AUTO_MERGE_EVALUATIONS = Counter(
            "codeguardian_auto_merge_evaluations_total",
            "Total auto-merge evaluation results",
            ["status"],
            registry=self.registry,
        )

        # 7. Failed reviews
        self.FAILED_REVIEWS = Counter(
            "codeguardian_review_failures_total",
            "Total failed review execution attempts",
            ["error_type"],
            registry=self.registry,
        )

    def record_review_processed(self, status: str = "completed") -> None:
        """Increment reviews processed counter by status ('completed', 'failed', 'auto_merged')."""
        self.REVIEWS_PROCESSED.labels(status=status).inc()

    def record_rule_finding(self, category: str, severity: str, count: int = 1) -> None:
        """Increment rule engine findings counter."""
        self.RULE_FINDINGS.labels(category=category, severity=severity).inc(count)

    def record_ai_review_latency(self, reviewer_name: str, duration_seconds: float) -> None:
        """Record AI reviewer latency duration in seconds."""
        self.REVIEW_LATENCY.labels(reviewer_name=reviewer_name).observe(duration_seconds)

    def record_tokens_consumed(
        self, prompt_tokens: int, completion_tokens: int, model_name: str = "gemini-2.5-flash"
    ) -> None:
        """Increment prompt, completion, and total tokens consumed counters."""
        self.TOKENS_CONSUMED.labels(token_type="prompt", model_name=model_name).inc(prompt_tokens)
        self.TOKENS_CONSUMED.labels(token_type="completion", model_name=model_name).inc(
            completion_tokens
        )
        self.TOKENS_CONSUMED.labels(token_type="total", model_name=model_name).inc(
            prompt_tokens + completion_tokens
        )

    def record_llm_cost(self, cost_usd: float, model_name: str = "gemini-2.5-flash") -> None:
        """Record estimated LLM cost in USD."""
        if cost_usd > 0:
            self.LLM_COST.labels(model_name=model_name).inc(cost_usd)

    def record_auto_merge_evaluation(self, status: str) -> None:
        """Increment auto-merge evaluation counter ('merged', 'rejected', 'failed_gates')."""
        self.AUTO_MERGE_EVALUATIONS.labels(status=status).inc()

    def record_failed_review(self, error_type: str) -> None:
        """Increment review failure counter by error_type."""
        self.FAILED_REVIEWS.labels(error_type=error_type).inc()

    def generate_metrics_exposition(self) -> tuple[bytes, str]:
        """Generate Prometheus exposition text format payload and content-type header.

        Returns:
            Tuple of (raw_bytes, content_type_str).
        """
        return generate_latest(self.registry), CONTENT_TYPE_LATEST


# Global Singleton Instance
metrics_service = PrometheusMetricsService()
