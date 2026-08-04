from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.analytics import ReviewAnalytics
from app.models.developer import Developer
from app.models.merge_request import MergeRequest
from app.models.repository import Repository
from app.models.review import Review
from app.models.review_finding import ReviewFinding
from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.developer_repo import DeveloperRepository
from app.repositories.repository_repo import RepositoryRepository
from app.repositories.review_repo import ReviewRepository

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", summary="Get Dashboard Overview Data")
def get_dashboard_overview(
    repository_id: int | None = None, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Retrieve complete Web UI dashboard overview dataset (Global or Repository-Filtered)."""
    analytics_repo = AnalyticsRepository(db)
    repo_repo = RepositoryRepository(db)
    dev_repo = DeveloperRepository(db)

    # 1. Registered Repositories
    repositories_list = []
    try:
        repos_db = repo_repo.list_all()
        for r in repos_db:
            if repository_id and r.id != repository_id:
                continue
            an = analytics_repo.get_by_repository_id(r.id)
            repositories_list.append({
                "id": r.id,
                "name": r.name,
                "path_with_namespace": r.path_with_namespace,
                "default_branch": r.default_branch,
                "average_score": an.average_score if an else 100.0,
                "total_reviews": an.total_reviews if an else 0,
                "critical_findings": an.critical_findings_count if an else 0,
            })
    except Exception:
        repositories_list = []

    # 2. Developer Leaderboard
    leaderboard_list = []
    try:
        devs_db = dev_repo.list_all()
        for d in devs_db:
            dev_mrs = db.scalars(
                select(MergeRequest.id).where(MergeRequest.author_username == d.username)
            ).all()
            if dev_mrs:
                dev_reviews = db.scalars(
                    select(Review).where(Review.merge_request_id.in_(dev_mrs))
                ).all()
                total_revs = len(dev_reviews)
                avg_sc = (sum(r.score for r in dev_reviews if r.score is not None) / total_revs) if total_revs > 0 else 100.0
                pass_count = sum(1 for r in dev_reviews if r.score and r.score >= 80)
                pass_rt = (pass_count / total_revs * 100) if total_revs > 0 else 100.0
            else:
                total_revs = 0
                avg_sc = 100.0
                pass_rt = 100.0

            badge = "Senior Engineer"
            if avg_sc >= 90 and total_revs >= 5:
                badge = "Master Architect"
            elif avg_sc >= 80:
                badge = "Code Guardian"

            leaderboard_list.append({
                "id": d.id,
                "username": d.username,
                "name": d.name or d.username,
                "total_reviews": total_revs,
                "avg_score": round(avg_sc, 1),
                "pass_rate": round(pass_rt, 1),
                "badge": badge,
            })
    except Exception:
        leaderboard_list = []

    # 3. Reviews List
    reviews_list = []
    try:
        review_stmt = (
            select(Review)
            .options(
                joinedload(Review.findings),
                joinedload(Review.merge_request).joinedload(MergeRequest.repository)
            )
            .order_by(Review.created_at.desc())
        )
        if repository_id:
            review_stmt = review_stmt.join(Review.merge_request).where(MergeRequest.repository_id == repository_id)

        reviews_db = db.scalars(review_stmt).unique().all()
        for rev in reviews_db:
            mr = rev.merge_request
            repo_name = mr.repository.path_with_namespace if (mr and mr.repository) else "repository"
            reviews_list.append({
                "id": rev.id,
                "repository": repo_name,
                "mr_title": mr.title if mr else f"Review #{rev.id}",
                "mr_iid": mr.gitlab_iid if mr else rev.id,
                "author": mr.author_username if mr else "developer",
                "score": rev.score if rev.score is not None else 100.0,
                "grade": rev.grade or "A",
                "status": rev.status,
                "duration_ms": rev.duration_ms or 0.0,
                "commit_sha": rev.commit_sha,
                "summary": rev.summary or "Code analysis complete.",
                "created_at": rev.created_at.isoformat() if rev.created_at else None,
                "findings": [
                    {
                        "id": f.id,
                        "title": f.title,
                        "severity": f.severity,
                        "category": f.category,
                        "file_path": f.file_path,
                        "line_number": f.line_number,
                        "description": f.description,
                        "suggestion": f.suggestion,
                    }
                    for f in rev.findings
                ]
            })
    except Exception:
        reviews_list = []

    # 4. Findings List
    findings_list = []
    try:
        finding_stmt = select(ReviewFinding).order_by(ReviewFinding.created_at.desc()).limit(100)
        findings_db = db.scalars(finding_stmt).all()
        findings_list = [
            {
                "id": f.id,
                "title": f.title,
                "severity": f.severity,
                "category": f.category,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "description": f.description,
                "suggestion": f.suggestion,
            }
            for f in findings_db
        ]
    except Exception:
        findings_list = []

    # 5. System Analytics & Overview
    total_reviews = len(reviews_list)
    avg_score = (sum(r["score"] for r in reviews_list) / total_reviews) if total_reviews > 0 else 0.0
    critical_count = sum(
        1 for f in findings_list if (f["severity"] or "").lower() == "critical"
    )
    auto_merged_count = sum(
        1 for r in reviews_list if r["score"] >= 80
    )
    auto_merge_rate = (auto_merged_count / total_reviews * 100.0) if total_reviews > 0 else 0.0

    return {
        "overview": {
            "total_reviews": total_reviews,
            "average_score": round(avg_score, 1),
            "critical_findings": critical_count,
            "auto_merge_rate": round(auto_merge_rate, 1),
        },
        "reviews": reviews_list,
        "repositories": repositories_list,
        "leaderboard": leaderboard_list,
        "findings": findings_list,
    }


@router.get("/reviews/{review_id}", summary="Get Detailed Interactive Review View")
def get_review_detail(review_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Retrieve detailed interactive review payload by ID."""
    review_repo = ReviewRepository(db)
    review = review_repo.get_by_id(review_id)
    if not review:
        raise HTTPException(status_code=404, detail=f"Review #{review_id} not found.")

    mr = review.merge_request
    repo_name = mr.repository.path_with_namespace if (mr and mr.repository) else "repository"

    return {
        "id": review.id,
        "merge_request_id": review.merge_request_id,
        "repository": repo_name,
        "mr_title": mr.title if mr else f"Review #{review.id}",
        "mr_iid": mr.gitlab_iid if mr else review.id,
        "author": mr.author_username if mr else "developer",
        "commit_sha": review.commit_sha,
        "score": review.score,
        "grade": review.grade,
        "risk_label": review.risk_label,
        "summary": review.summary,
        "duration_ms": review.duration_ms,
        "status": review.status,
        "findings": [
            {
                "id": f.id,
                "source": f.source,
                "category": f.category,
                "severity": f.severity,
                "title": f.title,
                "description": f.description,
                "suggestion": f.suggestion,
                "file_path": f.file_path,
                "line_number": f.line_number,
            }
            for f in review.findings
        ],
    }

