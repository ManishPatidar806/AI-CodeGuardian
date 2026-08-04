from dataclasses import dataclass, field
from pathlib import PurePosixPath

from app.repository_analysis.models import ParsedFile


@dataclass
class DependencyGraph:
    edges: dict[str, set[str]] = field(default_factory=dict)

    def add_file(
        self,
        file_path: str,
    ) -> None:
        self.edges.setdefault(file_path, set())

    def add_dependency(
        self,
        source: str,
        target: str,
    ) -> None:
        self.add_file(source)
        self.add_file(target)

        self.edges[source].add(target)

    def get_dependencies(
        self,
        file_path: str,
    ) -> set[str]:
        return self.edges.get(file_path, set())

    def get_dependents(
        self,
        file_path: str,
    ) -> set[str]:
        return {
            source
            for source, dependencies in self.edges.items()
            if file_path in dependencies
        }


class DependencyGraphBuilder:
    def build(
        self,
        parsed_files: list[ParsedFile],
    ) -> DependencyGraph:
        graph = DependencyGraph()

        python_files = {
            self._module_name(file.file_path): file.file_path
            for file in parsed_files
            if file.language == "python"
        }

        for parsed_file in parsed_files:
            graph.add_file(parsed_file.file_path)

            if parsed_file.language != "python":
                continue

            for imported_module in parsed_file.imports:
                target = self._resolve_import(
                    imported_module,
                    python_files,
                )

                if target is None:
                    continue

                if target == parsed_file.file_path:
                    continue

                graph.add_dependency(
                    parsed_file.file_path,
                    target,
                )

        return graph

    def _module_name(
        self,
        file_path: str,
    ) -> str:
        path = PurePosixPath(file_path)

        parts = list(path.parts)

        if not parts:
            return ""

        filename = parts[-1]

        if filename == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = path.stem

        return ".".join(parts)

    def _resolve_import(
        self,
        imported_module: str,
        python_files: dict[str, str],
    ) -> str | None:
        if imported_module in python_files:
            return python_files[imported_module]

        candidates = [
            (
                module_name,
                file_path,
            )
            for module_name, file_path in python_files.items()
            if module_name.startswith(f"{imported_module}.")
        ]

        if len(candidates) == 1:
            return candidates[0][1]

        return None
