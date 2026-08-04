from abc import ABC, abstractmethod

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.ai.schemas import AIReviewResponse
from app.core.settings import settings
from app.review_engine.finding import Finding


class BaseAIReviewer(ABC):
    def __init__(self) -> None:
        model = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.1,
        )

        self.model = model.with_structured_output(
            AIReviewResponse
        )

    @property
    @abstractmethod
    def reviewer_name(self) -> str:
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    def review(
        self,
        diff: str,
        repository_context: str,
    ) -> AIReviewResponse:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.system_prompt,
                ),
                (
                    "human",
                    """
Review the following pull request changes.

=== CHANGED CODE ===

{diff}

=== REPOSITORY CONTEXT ===

{repository_context}

Return only meaningful findings related to your
review responsibility.

Do not report purely stylistic preferences.

Do not invent files, functions, vulnerabilities,
or behavior that cannot reasonably be inferred
from the supplied code.

If there are no meaningful issues, return an
empty findings list.
""",
                ),
            ]
        )

        chain = prompt | self.model

        result = chain.invoke(
            {
                "diff": diff,
                "repository_context": repository_context,
            }
        )

        return result

    async def areview(
        self,
        diff: str,
        repository_context: str,
    ) -> AIReviewResponse:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.system_prompt,
                ),
                (
                    "human",
                    """
Review the following pull request changes.

=== CHANGED CODE ===

{diff}

=== REPOSITORY CONTEXT ===

{repository_context}

Return only meaningful findings related to your
review responsibility.

Do not report purely stylistic preferences.

Do not invent files, functions, vulnerabilities,
or behavior that cannot reasonably be inferred
from the supplied code.

If there are no meaningful issues, return an
empty findings list.
""",
                ),
            ]
        )

        chain = prompt | self.model

        result = await chain.ainvoke(
            {
                "diff": diff,
                "repository_context": repository_context,
            }
        )

        return result

    def to_findings(
        self,
        response: AIReviewResponse,
    ) -> list[Finding]:
        return [
            Finding(
                source=f"ai:{self.reviewer_name}",
                category=finding.category,
                severity=finding.severity,
                title=finding.title,
                description=finding.description,
                suggestion=finding.suggestion,
                file_path=finding.file_path,
                line_number=finding.line_number,
            )
            for finding in response.findings
        ]