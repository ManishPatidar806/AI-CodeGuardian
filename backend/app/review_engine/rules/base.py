from abc import ABC, abstractmethod
from app.review_engine.context import ReviewContext
from app.review_engine.finding import Finding


class ReviewRule(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def evaluate(
        self,
        context: ReviewContext,
    ) -> list[Finding]:
        raise NotImplementedError
