"""In-memory vector store — kept as a lightweight fallback for unit tests.

Production code uses Qdrant via database.vector.qdrant_client.
This module is only used when Qdrant is not available (e.g. during CI).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_engine.embeddings.embedding_model import EmbeddingModel
from ai_engine.vanilla_rag.scoring import cosine_similarity, relevance_score, query_coverage


@dataclass(frozen=True)
class VectorDocument:
    chunk_id:     str
    artifact_id:  str
    artifact_type:str
    title:        str
    content:      str
    metadata:     dict[str, Any]

    @property
    def embedding_text(self) -> str:
        meta = " ".join(str(v) for v in self.metadata.values())
        return f"{self.artifact_type} {self.title} {self.content} {meta}"


@dataclass(frozen=True)
class SearchResult:
    document:        VectorDocument
    similarity_score:float
    relevance_score: float = 0.0


class InMemoryVectorStore:
    """Index corpus embeddings once; exact cosine search at query time."""

    def __init__(
        self,
        documents: list[VectorDocument],
        embedding_model: EmbeddingModel,
    ) -> None:
        self.documents = documents
        self.embedding_model = embedding_model
        self._vectors = embedding_model.embed_many(
            d.embedding_text for d in documents
        )

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        results = [
            SearchResult(
                document=doc,
                similarity_score=cosine_similarity(query_embedding, vec),
            )
            for doc, vec in zip(self.documents, self._vectors)
        ]
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results[:min(top_k, len(results))]
