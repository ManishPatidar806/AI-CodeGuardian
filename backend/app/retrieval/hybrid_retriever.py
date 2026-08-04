from dataclasses import dataclass, field

from app.repository_analysis.dependency_graph import (
    DependencyGraph,
)
from app.repository_analysis.models import CodeChunk
from app.retrieval.retriever import (
    RetrievalResult,
    SemanticRetriever,
)


@dataclass(frozen=True)
class StructuralContext:
    file_path: str
    relationship: str
    chunks: list[CodeChunk] = field(default_factory=list)


@dataclass(frozen=True)
class RepositoryContext:
    semantic_results: list[RetrievalResult] = field(default_factory=list)

    structural_results: list[StructuralContext] = field(default_factory=list)


class HybridRetriever:
    def __init__(
        self,
        semantic_retriever: SemanticRetriever,
    ) -> None:
        self.semantic_retriever = semantic_retriever

    def retrieve(
        self,
        project_id: int,
        query: str,
        changed_files: list[str],
        dependency_graph: DependencyGraph,
        repository_chunks: list[CodeChunk],
        top_k: int = 5,
    ) -> RepositoryContext:
        semantic_results = self.semantic_retriever.search(
            project_id=project_id,
            query=query,
            top_k=top_k,
        )

        structural_results = self._get_structural_context(
            changed_files=changed_files,
            dependency_graph=dependency_graph,
        )

        return RepositoryContext(
            semantic_results=semantic_results,
            structural_results=structural_results,
        )

    def _build_chunk_lookup(
        self,
        repository_chunks: list[CodeChunk],
    ) -> dict[str, list[CodeChunk]]:
        lookup: dict[str, list[CodeChunk]] = {}

        for chunk in repository_chunks:
            lookup.setdefault(
                chunk.file_path,
                [],
            ).append(chunk)

        return lookup

    def _get_structural_context(
        self,
        changed_files: list[str],
        dependency_graph: DependencyGraph,
        repository_chunks: list[CodeChunk],
    ) -> list[StructuralContext]:
        results: list[StructuralContext] = []

        seen: set[tuple[str, str]] = set()

        chunk_lookup = self._build_chunk_lookup(repository_chunks)

        for changed_file in changed_files:
            dependencies = dependency_graph.get_dependencies(changed_file)

            for file_path in dependencies:
                key = (
                    file_path,
                    "dependency",
                )

                if key in seen:
                    continue

                seen.add(key)

                results.append(
                    StructuralContext(
                        file_path=file_path,
                        relationship="dependency",
                        chunks=chunk_lookup.get(
                            file_path,
                            [],
                        ),
                    )
                )

            dependents = dependency_graph.get_dependents(changed_file)

            for file_path in dependents:
                key = (
                    file_path,
                    "dependent",
                )

                if key in seen:
                    continue

                seen.add(key)

                results.append(
                    StructuralContext(
                        file_path=file_path,
                        relationship="dependent",
                        chunks=chunk_lookup.get(
                            file_path,
                            [],
                        ),
                    )
                )

        return results
