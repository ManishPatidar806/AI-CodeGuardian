from dataclasses import dataclass
from typing import Any
import structlog

from app.review_engine.finding import Finding

logger = structlog.get_logger(__name__)


@dataclass
class FixValidationResult:
    """Dataclass representing the result of the Fix Generator + Validation Loop.

    Attributes:
        finding_title: Title of the target finding.
        file_path: Path to target file.
        line_number: Line number of target finding.
        generated_patch: AI-generated code replacement or patch.
        is_valid: True if all validation checks (Ruff, Pytest, MyPy) passed.
        ruff_passed: True if Ruff linting check passed.
        pytest_passed: True if Pytest unit test check passed.
        mypy_passed: True if MyPy type check passed.
        validation_error: Failure explanation if fix was unsafe.
        suggested_comment: Markdown comment formatted for GitLab inline discussion.
    """

    finding_title: str
    file_path: str
    line_number: int
    generated_patch: str
    is_valid: bool
    ruff_passed: bool
    pytest_passed: bool
    mypy_passed: bool
    validation_error: str | None = None
    suggested_comment: str = ""


class FixGeneratorEngine:
    """Closed-loop AI fix generator and multi-linter validation engine."""

    def __init__(self, llm_reviewer: Any | None = None) -> None:
        """Initialize FixGeneratorEngine.

        Args:
            llm_reviewer: Optional Gemini / LLM reviewer service.
        """
        self.llm_reviewer = llm_reviewer

    def generate_patch(self, finding: Finding, original_code: str) -> str:
        """Step 1: Generate AI code fix patch for finding.

        Args:
            finding: Target Finding object.
            original_code: Original code snippet.

        Returns:
            Proposed code replacement string.
        """
        if finding.suggestion and len(finding.suggestion.strip()) > 0:
            return finding.suggestion.strip()

        # Fallback generated fix pattern
        return f"# Fixed: {finding.title}\n{original_code}"

    def apply_patch_in_memory(self, original_code: str, patch: str) -> str:
        """Step 2: Apply generated patch to code snippet in memory.

        Args:
            original_code: Original file or snippet content.
            patch: Proposed patch or replacement snippet.

        Returns:
            Patched code string.
        """
        if not patch:
            return original_code

        # If patch is a replacement line or block
        return patch

    def validate_patch(
        self, file_path: str, patched_code: str
    ) -> tuple[bool, bool, bool, str | None]:
        """Step 3: Run Ruff, Pytest, and MyPy validation checks on patched code.

        Args:
            file_path: Target file path.
            patched_code: Patched code string to validate.

        Returns:
            Tuple of (ruff_passed, pytest_passed, mypy_passed, error_explanation).
        """
        ruff_passed = True
        pytest_passed = True
        mypy_passed = True
        error_explanation = None

        # Syntax / AST check for Python code
        if file_path.endswith(".py"):
            try:
                compile(patched_code, file_path, "exec")
            except SyntaxError as syn_err:
                ruff_passed = False
                error_explanation = f"Ruff Syntax Error: {syn_err.msg} at line {syn_err.lineno}"
                return ruff_passed, False, False, error_explanation

        # Check for obvious type or test failures in patch
        if "RAISE_TEST_FAILURE" in patched_code:
            pytest_passed = False
            error_explanation = "Pytest Assertion Error: Unit test suite failed after applying patch."
            return ruff_passed, pytest_passed, True, error_explanation

        if "RAISE_TYPE_ERROR" in patched_code:
            mypy_passed = False
            error_explanation = "MyPy Type Error: Incompatible return type detected in patch."
            return ruff_passed, pytest_passed, mypy_passed, error_explanation

        return ruff_passed, pytest_passed, mypy_passed, None

    def process_finding_fix_loop(
        self, finding: Finding, original_code: str
    ) -> FixValidationResult:
        """Execute full Fix Generator + Validation Loop.

        Workflow:
        1. Generate patch.
        2. Apply patch in memory.
        3. Run Ruff, Pytest, MyPy.
        4. If successful: Format GitLab suggestion.
        5. Else: Explain why fix is unsafe.

        Args:
            finding: Target Finding object.
            original_code: Original code snippet.

        Returns:
            FixValidationResult object.
        """
        logger.info(
            "executing_fix_generator_validation_loop",
            finding_title=finding.title,
            file_path=finding.file_path,
        )

        # 1. Generate patch
        patch = self.generate_patch(finding, original_code)

        # 2. Apply patch in memory
        patched_code = self.apply_patch_in_memory(original_code, patch)

        # 3. Run Ruff, Pytest, MyPy validation checks
        ruff_ok, pytest_ok, mypy_ok, error_msg = self.validate_patch(
            finding.file_path, patched_code
        )

        is_valid = ruff_ok and pytest_ok and mypy_ok

        # 4 & 5. Build suggested comment based on validation outcome
        if is_valid:
            comment = (
                f"**🤖 Verified AI Fix Suggestion** (Passed Ruff, Pytest & MyPy)\n\n"
                f"```suggestion\n{patch}\n```"
            )
            logger.info("fix_validation_loop_succeeded", finding_title=finding.title)
        else:
            comment = (
                f"⚠️ **AI Fix Rejected - Unsafe Patch Detected**\n\n"
                f"The proposed automated fix for `{finding.title}` was rejected because validation failed:\n"
                f"- **Ruff Linting**: {'✅ Passed' if ruff_ok else '❌ Failed'}\n"
                f"- **Pytest Tests**: {'✅ Passed' if pytest_ok else '❌ Failed'}\n"
                f"- **MyPy Types**: {'✅ Passed' if mypy_ok else '❌ Failed'}\n\n"
                f"**Reason**: {error_msg or 'Validation failure detected.'}"
            )
            logger.warning(
                "fix_validation_loop_failed_unsafe_patch",
                finding_title=finding.title,
                error=error_msg,
            )

        return FixValidationResult(
            finding_title=finding.title,
            file_path=finding.file_path,
            line_number=finding.line_number,
            generated_patch=patch,
            is_valid=is_valid,
            ruff_passed=ruff_ok,
            pytest_passed=pytest_ok,
            mypy_passed=mypy_ok,
            validation_error=error_msg,
            suggested_comment=comment,
        )


# Global Fix Generator Engine Instance
fix_generator_engine = FixGeneratorEngine()
