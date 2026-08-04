from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.review_engine.finding import Finding
from app.review_engine.fix_generator import fix_generator_engine

router = APIRouter(prefix="/fixes", tags=["Fix Generator"])


class FixGenerationRequest(BaseModel):
    """Pydantic request payload for Fix Generator + Validation Loop."""

    title: str = Field(..., description="Finding title")
    description: str = Field(..., description="Finding description")
    file_path: str = Field(..., description="Target file path")
    line_number: int = Field(default=1, ge=1, description="Target line number")
    category: str = Field(default="clean_code", description="Finding category")
    severity: str = Field(default="medium", description="Finding severity")
    suggestion: str = Field(default="", description="Proposed fix code snippet")
    original_code: str = Field(..., description="Original code snippet")


@router.post("/validate", summary="Run Fix Generator & Validation Loop")
def generate_and_validate_fix(payload: FixGenerationRequest) -> dict[str, Any]:
    """Execute closed-loop AI fix generation and multi-linter validation (Ruff, Pytest, MyPy).

    Args:
        payload: FixGenerationRequest payload.

    Returns:
        FixValidationResult dictionary.
    """
    try:
        finding = Finding(
            source="ai_reviewer",
            title=payload.title,
            description=payload.description,
            file_path=payload.file_path,
            line_number=payload.line_number,
            category=payload.category,
            severity=payload.severity,
            suggestion=payload.suggestion,
        )

        result = fix_generator_engine.process_finding_fix_loop(finding, payload.original_code)

        return {
            "finding_title": result.finding_title,
            "file_path": result.file_path,
            "line_number": result.line_number,
            "generated_patch": result.generated_patch,
            "is_valid": result.is_valid,
            "ruff_passed": result.ruff_passed,
            "pytest_passed": result.pytest_passed,
            "mypy_passed": result.mypy_passed,
            "validation_error": result.validation_error,
            "suggested_comment": result.suggested_comment,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Fix generation loop failed: {exc}",
        ) from exc
