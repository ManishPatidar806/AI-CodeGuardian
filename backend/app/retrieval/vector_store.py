import hashlib

import chromadb

from app.core.settings import settings
from app.repository_analysis.models import CodeChunk
from app.retrieval.embeddings import EmbeddingGenerator


class CodeVectorStore:
    def __init__(
        self,
        embedding_generator: EmbeddingGenerator,
    ) -> None:
        self.embedding_generator = embedding_generator

        self.client = chromadb.PersistentClient(path=settings.chroma_path)

    def get_collection(
        self,
        project_id: int,
    ):
        return self.client.get_or_create_collection(name=f"project_{project_id}")

    def index_chunks(
        self,
        project_id: int,
        chunks: list[CodeChunk],
    ) -> int:
        if not chunks:
            return 0

        collection = self.get_collection(project_id)

        documents = [chunk.content for chunk in chunks]

        embeddings = self.embedding_generator.embed_documents(documents)

        ids = [
            self._chunk_id(
                project_id,
                chunk,
            )
            for chunk in chunks
        ]

        metadatas = [self._metadata(chunk) for chunk in chunks]

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return len(chunks)

    def _chunk_id(
        self,
        project_id: int,
        chunk: CodeChunk,
    ) -> str:
        value = (
            f"{project_id}:"
            f"{chunk.file_path}:"
            f"{chunk.symbol_type}:"
            f"{chunk.symbol_name}:"
            f"{chunk.start_line}:"
            f"{chunk.end_line}"
        )

        return hashlib.sha256(value.encode()).hexdigest()

    def _metadata(
        self,
        chunk: CodeChunk,
    ) -> dict[str, str | int]:
        metadata: dict[str, str | int] = {
            "file_path": chunk.file_path,
            "language": chunk.language,
        }

        if chunk.symbol_name is not None:
            metadata["symbol_name"] = chunk.symbol_name

        if chunk.symbol_type is not None:
            metadata["symbol_type"] = chunk.symbol_type

        if chunk.parent_name is not None:
            metadata["parent_name"] = chunk.parent_name

        if chunk.start_line is not None:
            metadata["start_line"] = chunk.start_line

        if chunk.end_line is not None:
            metadata["end_line"] = chunk.end_line

        return metadata
