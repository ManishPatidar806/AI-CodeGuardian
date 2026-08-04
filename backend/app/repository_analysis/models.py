from dataclasses import dataclass, field


@dataclass(frozen=True)
class CodeSymbol:
    name: str
    symbol_type: str
    start_line: int
    end_line: int
    content: str
    parent_name: str | None = None


@dataclass(frozen=True)
class ParsedFile:
    file_path: str
    language: str
    content: str
    imports: list[str] = field(default_factory=list)
    symbols: list[CodeSymbol] = field(default_factory=list)


@dataclass(frozen=True)
class CodeChunk:
    file_path: str
    language: str
    content: str
    symbol_name: str | None = None
    symbol_type: str | None = None
    parent_name: str | None = None
    start_line: int | None = None
    end_line: int | None = None


@dataclass(frozen=True)
class RepositoryAnalysis:
    parsed_files: list[ParsedFile]
    chunks: list[CodeChunk]
