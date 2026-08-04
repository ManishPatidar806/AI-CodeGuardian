from typing import Literal
from pydantic import BaseModel, Field

Severity = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

class AIFinding(BaseModel):
    category:str
    severity:Severity
    title:str
    description:str
    suggestion:str | None=None
    file_path:str | None=None
    line_number:int|None=Field(
        default=None,
        description=(
            "New-file line number when it can be "
            "determined reliably."
        )
    )

class AIReviewResponse(BaseModel):
    summary:str
    findings:list[AIFinding]=Field(
        default_factory=list
    )
    