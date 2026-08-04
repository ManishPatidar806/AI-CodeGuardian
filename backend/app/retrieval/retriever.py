from dataclasses import dataclass

from app.retrieval.embeddings import EmbeddingGenerator
from app.retrieval.vector_store import CodeVectorStore


@dataclass(frozen=True)
class RetrievalResult:
    content: str
    file_path: str
    language: str

    score: float

    symbol_name: str | None = None
    symbol_type: str | None = None
    parent_name: str | None = None

    start_line: int | None = None
    end_line: int | None = None


class SemanticRetriever:
    def __init__(
        self,
        embedding_generator: EmbeddingGenerator,
        vector_store: CodeVectorStore,
    ) -> None:
        self.embedding_generator = embedding_generator
        self.vector_store = vector_store

    def search(
        self,
        project_id: int,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        if not query.strip():
            return []

        query_embedding = self.embedding_generator.embed_query(query)

        collection = self.vector_store.get_collection(project_id)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        documents = results.get("documents") or [[]]
        metadatas = results.get("metadatas") or [[]]
        distances = results.get("distances") or [[]]

        if not documents:
            return []

        retrieved: list[RetrievalResult] = []

        for document, metadata, distance in zip(
            documents[0],
            metadatas[0],
            distances[0],
            strict=True,
        ):
            metadata = metadata or {}

            retrieved.append(
                RetrievalResult(
                    content=document,
                    file_path=str(metadata.get("file_path", "")),
                    language=str(metadata.get("language", "")),
                    score=float(distance),
                    symbol_name=self._optional_str(metadata.get("symbol_name")),
                    symbol_type=self._optional_str(metadata.get("symbol_type")),
                    parent_name=self._optional_str(metadata.get("parent_name")),
                    start_line=self._optional_int(metadata.get("start_line")),
                    end_line=self._optional_int(metadata.get("end_line")),
                )
            )

        return retrieved

    @staticmethod
    def _optional_str(
        value: object,
    ) -> str | None:
        if value is None:
            return None

        return str(value)

    @staticmethod
    def _optional_int(
        value: object,
    ) -> int | None:
        if value is None:
            return None

        return int(value)
