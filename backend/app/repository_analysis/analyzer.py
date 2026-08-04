import structlog

from app.repository_analysis.chunker import CodeChunker
from app.repository_analysis.fetcher import RepositoryFile
from app.repository_analysis.file_parser import PythonFileParser
from app.repository_analysis.language import detect_language
from app.repository_analysis.models import (
    CodeChunk,
    ParsedFile,
    RepositoryAnalysis,
)


logger = structlog.get_logger(__name__)


class RepositoryAnalyzer:
    def __init__(self) -> None:
        self.python_parser = PythonFileParser()
        self.chunker = CodeChunker()

    def analyze(
        self,
        files: list[RepositoryFile],
    ) -> RepositoryAnalysis:
        parsed_files: list[ParsedFile] = []
        chunks: list[CodeChunk] = []

        for file in files:
            parsed_file = self.parse_file(
                file_path=file.path,
                content=file.content,
            )

            if parsed_file is None:
                continue

            parsed_files.append(parsed_file)

            chunks.extend(self.chunker.create_chunks(parsed_file))

        logger.info(
            "repository_analysis_completed",
            files=len(parsed_files),
            chunks=len(chunks),
        )

        return RepositoryAnalysis(
            parsed_files=parsed_files,
            chunks=chunks,
        )

    def parse_file(
        self,
        file_path: str,
        content: str,
    ) -> ParsedFile | None:
        language = detect_language(file_path)

        if language is None:
            return None

        if language != "python":
            logger.debug(
                "parser_not_implemented",
                file_path=file_path,
                language=language,
            )
            return None

        try:
            return self.python_parser.parse(
                file_path=file_path,
                content=content,
            )

        except SyntaxError as exc:
            logger.warning(
                "source_parse_failed",
                file_path=file_path,
                error=str(exc),
            )

            return None
