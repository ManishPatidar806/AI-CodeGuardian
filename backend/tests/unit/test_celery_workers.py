from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from app.workers.celery_app import celery_app
from app.workers.tasks import (
    generate_embeddings_task,
    index_repository_task,
    periodic_cleanup_task,
    send_slack_notification_task,
)


def test_celery_app_configuration() -> None:
    """Verify Celery application setup, Beat schedule, and serialization settings."""
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.accept_content == ["json"]
    assert celery_app.conf.result_serializer == "json"
    assert "daily_periodic_cleanup_task" in celery_app.conf.beat_schedule


def test_index_repository_task(tmp_path: Path) -> None:
    """Verify index_repository_task execution and caching."""
    dummy_repo = tmp_path / "my_repo"
    dummy_repo.mkdir()
    (dummy_repo / "main.py").write_text("def hello(): pass")

    with patch("app.workers.tasks.EmbeddingGenerator") as mock_embed_cls:
        mock_instance = MagicMock()
        mock_instance.generate_embeddings.return_value = [[0.1, 0.2]]
        mock_embed_cls.return_value = mock_instance

        # Call task eagerly
        res = index_repository_task.apply(
            args=(str(dummy_repo), 101, "sha_test_101")
        ).get()

        assert res["status"] in ["indexed", "cached"]
        assert res["project_id"] == 101


def test_generate_embeddings_task() -> None:
    """Verify generate_embeddings_task execution."""
    chunks = ["def foo(): pass", "def bar(): pass"]

    with patch("app.workers.tasks.EmbeddingGenerator") as mock_embed_cls:
        mock_instance = MagicMock()
        mock_instance.generate_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_embed_cls.return_value = mock_instance

        res = generate_embeddings_task.apply(args=(chunks, "sentence-transformers")).get()
        assert res["status"] == "completed"
        assert res["total_chunks"] == 2


def test_send_slack_notification_task() -> None:
    """Verify send_slack_notification_task execution."""
    payload_dict = {
        "repository": "owner/repo",
        "developer": "alice",
        "score": 95.0,
        "grade": "A+",
        "summary": "Clean code!",
        "findings": [],
        "mr_url": "https://gitlab.com/owner/repo/-/merge_requests/10",
        "mr_title": "Update Auth",
        "branch_name": "feature/auth",
    }

    with patch("app.workers.tasks.SlackNotifier") as mock_notifier_cls:
        mock_instance = MagicMock()
        mock_instance.send_review_notification.return_value = {"ok": True}
        mock_notifier_cls.return_value = mock_instance

        res = send_slack_notification_task.apply(args=(payload_dict,)).get()
        assert res["status"] == "delivered"
        assert res["repository"] == "owner/repo"


def test_periodic_cleanup_task() -> None:
    """Verify periodic_cleanup_task cache purging."""
    with patch("app.workers.tasks.CodeGuardianCache") as mock_cache_cls:
        mock_instance = MagicMock()
        mock_instance.cache_service.delete_by_pattern.return_value = 15
        mock_cache_cls.return_value = mock_instance

        res = periodic_cleanup_task.apply().get()
        assert res["status"] == "completed"
        assert res["purged_cache_keys"] == 15


def test_retry_mechanism_on_task_failure() -> None:
    """Verify index_repository_task retries on exception."""
    with patch("app.workers.tasks.CodeGuardianCache") as mock_cache_cls:
        mock_cache_cls.side_effect = RuntimeError("Database connection timed out")

        with pytest.raises(Exception):
            index_repository_task.apply(args=("/invalid/path", 999, "sha_fail")).get()
