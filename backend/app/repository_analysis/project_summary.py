from collections import Counter
from dataclasses import dataclass

from app.repository_analysis.dependency_graph import DependencyGraph
from app.repository_analysis.models import RepositoryAnalysis


@dataclass(frozen=True)
class ProjectSummary:
    total_files: int
    total_chunks: int

    languages: dict[str, int]
    symbol_types: dict[str, int]

    total_dependencies: int

    most_connected_files: list[str]


class ProjectSummaryBuilder:
    def build(
        self,
        analysis: RepositoryAnalysis,
        graph: DependencyGraph,
    ) -> ProjectSummary:
        languages = Counter(file.language for file in analysis.parsed_files)

        symbol_types = Counter(
            chunk.symbol_type for chunk in analysis.chunks if chunk.symbol_type
        )

        total_dependencies = sum(
            len(dependencies) for dependencies in graph.edges.values()
        )

        connected = sorted(
            graph.edges.items(),
            key=lambda item: len(item[1]),
            reverse=True,
        )

        most_connected_files = [
            file_path for file_path, dependencies in connected[:10] if dependencies
        ]

        return ProjectSummary(
            total_files=len(analysis.parsed_files),
            total_chunks=len(analysis.chunks),
            languages=dict(languages),
            symbol_types=dict(symbol_types),
            total_dependencies=total_dependencies,
            most_connected_files=most_connected_files,
        )
