from app.retrieval.hybrid_retriever import (
    RepositoryContext,
)


class AIContextBuilder:
    def build(
        self,
        context: RepositoryContext,
        max_semantic_results: int = 5,
        max_structural_files: int = 3,
        max_chunks_per_file: int = 2,
    ) -> str:
        sections: list[str] = []

        semantic_results = (
            context.semantic_results[
                :max_semantic_results
            ]
        )

        if semantic_results:
            sections.append(
                "=== SEMANTICALLY RELATED CODE ==="
            )

        for result in semantic_results:
            sections.append(
                self._format_code(
                    file_path=result.file_path,
                    symbol=result.symbol_name,
                    start_line=result.start_line,
                    end_line=result.end_line,
                    content=result.content,
                )
            )

        structural_results = (
            context.structural_results[
                :max_structural_files
            ]
        )

        if structural_results:
            sections.append(
                "=== STRUCTURALLY RELATED CODE ==="
            )

        for result in structural_results:
            sections.append(
                (
                    f"\nRelated file: {result.file_path}\n"
                    f"Relationship: {result.relationship}"
                )
            )

            for chunk in result.chunks[
                :max_chunks_per_file
            ]:
                sections.append(
                    self._format_code(
                        file_path=chunk.file_path,
                        symbol=chunk.symbol_name,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                        content=chunk.content,
                    )
                )

        return "\n\n".join(sections)

    def _format_code(
        self,
        file_path: str,
        symbol: str | None,
        start_line: int | None,
        end_line: int | None,
        content: str,
    ) -> str:
        return (
            f"FILE: {file_path}\n"
            f"SYMBOL: {symbol or 'N/A'}\n"
            f"LINES: {start_line}-{end_line}\n"
            f"```text\n"
            f"{content}\n"
            f"```"
        )