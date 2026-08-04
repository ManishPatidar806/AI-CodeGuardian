from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    source: str
    category: str
    severity: str

    title: str
    description: str
    suggestion: str | None = None

    file_path: str | None = None
    line_number: int | None = None
