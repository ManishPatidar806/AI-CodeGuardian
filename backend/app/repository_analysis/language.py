from pathlib import Path


LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}


def detect_language(
    file_path: str,
) -> str | None:
    suffix = Path(file_path).suffix.lower()

    return LANGUAGE_BY_EXTENSION.get(suffix)
