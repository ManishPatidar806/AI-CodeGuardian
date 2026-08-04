from sentence_transformers import SentenceTransformer

from app.core.settings import settings


class EmbeddingGenerator:
    def __init__(self) -> None:
        self.model = SentenceTransformer(settings.embedding_model)

    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]:
        if not documents:
            return []

        embeddings = self.model.encode(
            documents,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()

    def embed_query(
        self,
        query: str,
    ) -> list[float]:
        embedding = self.model.encode(
            query,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embedding.tolist()
