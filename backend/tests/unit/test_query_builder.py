from app.retrieval.query_builder import GeneratedQueries, QueryBuilder
from app.review_engine.context import ReviewContext


def test_build_queries_from_title_and_description() -> None:
    """Verify QueryBuilder extracts keywords from title and description."""
    builder = QueryBuilder()
    result = builder.build_queries(
        title="Add JWT Authentication Middleware",
        description="Implements secure token verification and user scope validation.",
    )

    assert isinstance(result, GeneratedQueries)
    assert "jwt" in result.primary_query.lower()
    assert "authentication" in result.primary_query.lower()
    assert "middleware" in result.primary_query.lower()
    assert "verification" in result.primary_query.lower()
    assert len(result.keywords) > 0


def test_branch_name_tokenization() -> None:
    """Verify branch names like feature/jira-102-auth-jwt are tokenized correctly."""
    builder = QueryBuilder()
    result = builder.build_queries(
        title="Fix bug",
        branch_name="feature/jira-102-auth-jwt-migration",
    )

    keywords = [k.lower() for k in result.keywords]
    assert "feature" in keywords
    assert "auth" in keywords
    assert "jwt" in keywords
    assert "migration" in keywords


def test_commit_messages_parsing() -> None:
    """Verify commit messages are parsed and integrated into retrieval queries."""
    builder = QueryBuilder()
    result = builder.build_queries(
        title="Refactor DB query layer",
        commit_messages=[
            "feat: optimize connection pool timeout",
            "fix: resolve connection leak in retry loop",
        ],
    )

    assert "connection" in result.primary_query.lower()
    assert "pool" in result.primary_query.lower()
    assert "timeout" in result.primary_query.lower()
    assert "leak" in result.primary_query.lower()


def test_code_symbol_extraction_from_diff() -> None:
    """Verify code symbols (classes, functions, methods) are extracted from git diff additions (+)."""
    builder = QueryBuilder()
    sample_diff = """
--- a/app/services/auth.py
+++ b/app/services/auth.py
@@ -10,6 +10,12 @@
+class SecurityReviewer:
+    def authenticate_user(self, token: str) -> bool:
+        pass
+
+async def verify_jwt_signature(secret: str) -> bool:
+    return True
"""

    result = builder.build_queries(
        title="Update auth service",
        git_diff=sample_diff,
        changed_files=["app/services/auth.py"],
    )

    assert "SecurityReviewer" in result.extracted_symbols
    assert "authenticate_user" in result.extracted_symbols
    assert "verify_jwt_signature" in result.extracted_symbols
    assert "SecurityReviewer" in result.symbol_query


def test_file_path_keyword_extraction() -> None:
    """Verify file paths contribute relevant directory and filename tokens."""
    builder = QueryBuilder()
    result = builder.build_queries(
        title="Update user service",
        changed_files=[
            "app/repositories/user_repository.py",
            "app/services/payment_service.py",
        ],
    )

    keywords = [k.lower() for k in result.keywords]
    assert "repositories" in keywords
    assert "user" in keywords
    assert "repository" in keywords
    assert "payment" in keywords
    assert "services" in keywords


def test_build_from_context() -> None:
    """Verify QueryBuilder works directly with a ReviewContext object."""
    builder = QueryBuilder()
    context = ReviewContext(
        project_id=1,
        mr_iid=42,
        title="Implement Redis Caching Layer",
        description="Add cache decorator for high-frequency database lookups.",
        source_branch="feature/redis-cache",
        traget_branch="main",
        commits=[{"message": "add redis client initial setup"}],
        diffs=[
            {
                "new_path": "app/core/cache.py",
                "diff": "+class RedisCache:\n+    def get_val(self, key: str):\n+        pass",
            }
        ],
    )

    result = builder.build_from_context(context)

    assert isinstance(result, GeneratedQueries)
    assert "redis" in result.primary_query.lower()
    assert "cache" in result.primary_query.lower()
    assert "RedisCache" in result.extracted_symbols
    assert "get_val" in result.extracted_symbols


def test_build_unified_query_convenience_method() -> None:
    """Verify build_unified_query returns a single non-empty query string."""
    builder = QueryBuilder()
    unified = builder.build_unified_query(
        title="Optimize GraphQL resolver performance",
        description="Batch database queries using DataLoader pattern.",
    )

    assert isinstance(unified, str)
    assert "graphql" in unified.lower()
    assert "dataloader" in unified.lower()


def test_query_length_truncation() -> None:
    """Verify max_query_length bounds the primary query length."""
    builder = QueryBuilder(max_query_length=50)
    result = builder.build_queries(
        title="Very long feature description title with multiple distinct terms",
        description="Extensive description detailing architectural modifications across multiple services.",
    )

    assert len(result.primary_query) <= 50
