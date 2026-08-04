from pathlib import Path
import sys

# Add scripts directory to sys.path
scripts_dir = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from verify_production_readiness import ProductionReadinessVerifier  # noqa: E402


def test_production_readiness_verifier() -> None:
    """Verify ProductionReadinessVerifier runs checks and returns valid report."""
    verifier = ProductionReadinessVerifier()
    report = verifier.run_all_checks()

    assert "status" in report
    assert "total_checks" in report
    assert "checks" in report
    assert report["total_checks"] == 3


def test_dockerfile_integrity() -> None:
    """Verify backend Dockerfile exists and contains multi-stage build instructions."""
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    dockerfile_path = root_dir / "backend" / "Dockerfile"

    assert dockerfile_path.exists()
    content = dockerfile_path.read_text(encoding="utf-8")

    assert "FROM python:3.12-slim AS builder" in content
    assert "FROM python:3.12-slim AS runner" in content
    assert "USER appuser" in content
    assert "HEALTHCHECK" in content


def test_docker_compose_integrity() -> None:
    """Verify docker-compose.prod.yml exists and contains expected enterprise services."""
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    compose_path = root_dir / "docker-compose.prod.yml"

    assert compose_path.exists()
    content = compose_path.read_text(encoding="utf-8")

    assert "postgres:" in content
    assert "redis:" in content
    assert "backend:" in content
    assert "celery_worker:" in content
    assert "prometheus:" in content
    assert "grafana:" in content


def test_kubernetes_manifests() -> None:
    """Verify Kubernetes manifest YAML files exist in k8s/ directory."""
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    k8s_dir = root_dir / "k8s"

    manifests = [
        "namespace.yaml",
        "configmap.yaml",
        "secret.yaml",
        "deployment.yaml",
        "service.yaml",
        "hpa.yaml",
    ]

    for manifest in manifests:
        path = k8s_dir / manifest
        assert path.exists(), f"Missing K8s manifest: {manifest}"
        assert len(path.read_text(encoding="utf-8")) > 10


def test_helm_chart_structure() -> None:
    """Verify Helm Chart structure exists under helm/ai-codeguardian/."""
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    helm_dir = root_dir / "helm" / "ai-codeguardian"

    chart_yaml = helm_dir / "Chart.yaml"
    values_yaml = helm_dir / "values.yaml"
    deploy_tmpl = helm_dir / "templates" / "deployment.yaml"
    svc_tmpl = helm_dir / "templates" / "service.yaml"

    assert chart_yaml.exists()
    assert values_yaml.exists()
    assert deploy_tmpl.exists()
    assert svc_tmpl.exists()
