from pathlib import Path


class RepositoryFileFilter:
    SUPPORTED_EXTENSIONS = {
        ".py",
        ".java",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
    }

    IGNORED_DIRECTORIES = {
        ".git",
        ".idea",
        ".vscode",
        ".venv",
        "venv",
        "node_modules",
        "dist",
        "build",
        "coverage",
        "__pycache__",
    }

    IGNORED_FILES = {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
    }

    def should_analyze(
        self,
        file_path: str,
    ) -> bool:
        path = Path(file_path)

        if path.name in self.IGNORED_FILES:
            return False

        if any(part in self.IGNORED_DIRECTORIES for part in path.parts):
            return False

        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS
