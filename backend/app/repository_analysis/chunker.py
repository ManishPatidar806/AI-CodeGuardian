from app.repository_analysis.models import (
    CodeChunk,
    ParsedFile,
)


class CodeChunker:
    def create_chunks(
        self,
        parsed_file: ParsedFile,
    ) -> list[CodeChunk]:
        chunks: list[CodeChunk] = []

        for symbol in parsed_file.symbols:
            chunks.append(
                CodeChunk(
                    file_path=parsed_file.file_path,
                    language=parsed_file.language,
                    content=symbol.content,
                    symbol_name=symbol.name,
                    symbol_type=symbol.symbol_type,
                    parent_name=symbol.parent_name,
                    start_line=symbol.start_line,
                    end_line=symbol.end_line,
                )
            )

        if not chunks and parsed_file.content.strip():
            chunks.append(
                CodeChunk(
                    file_path=parsed_file.file_path,
                    language=parsed_file.language,
                    content=parsed_file.content,
                    start_line=1,
                    end_line=len(parsed_file.content.splitlines()),
                )
            )

        return chunks
