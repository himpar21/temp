"""Qdrant vector database client.

Handles collection management, upsert, and semantic search.
Uses the Ollama nomic-embed-text model for embeddings — fully local,
no external API required.

Environment variables:
    QDRANT_HOST        — Qdrant server host       (default: localhost)
    QDRANT_PORT        — Qdrant REST port          (default: 6333)
    QDRANT_COLLECTION  — collection name           (default: test_management_chunks)
    OLLAMA_BASE_URL    — Ollama server URL         (default: http://localhost:11434)
    OLLAMA_EMBED_MODEL — embedding model name      (default: nomic-embed-text)
    OLLAMA_TIMEOUT     — request timeout seconds   (default: 120)
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

logger = logging.getLogger(__name__)

# ── defaults ──────────────────────────────────────────────────────────────────
_DEFAULT_HOST        = "localhost"
_DEFAULT_PORT        = 6333
_DEFAULT_COLLECTION  = "test_management_chunks"
_DEFAULT_EMBED_MODEL = "nomic-embed-text"
_DEFAULT_VECTOR_SIZE = 768    # nomic-embed-text output dimension
_DEFAULT_TIMEOUT     = 120


@dataclass(frozen=True)
class SearchResult:
    """A single result returned by semantic search."""
    id: str
    score: float
    text: str
    document_id: str
    filename: str
    entity_ids: list[str]
    metadata: dict[str, Any]


class QdrantVectorClient:
    """Qdrant client with Ollama-powered embeddings."""

    def __init__(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        collection: str | None = None,
        embed_model: str | None = None,
        ollama_base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.host        = host        or os.getenv("QDRANT_HOST",       _DEFAULT_HOST)
        self.port        = port        or int(os.getenv("QDRANT_PORT",   str(_DEFAULT_PORT)))
        self.collection  = collection  or os.getenv("QDRANT_COLLECTION", _DEFAULT_COLLECTION)
        self.embed_model = embed_model or os.getenv("OLLAMA_EMBED_MODEL",_DEFAULT_EMBED_MODEL)
        self.timeout     = timeout     or int(os.getenv("OLLAMA_TIMEOUT",str(_DEFAULT_TIMEOUT)))

        raw_base = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._ollama_embed_url = raw_base.rstrip("/") + "/api/embeddings"

        self._client = QdrantClient(host=self.host, port=self.port)
        self._ensure_collection()

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    def embed(self, text: str) -> list[float]:
        """Embed a single text using Ollama nomic-embed-text."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                self._ollama_embed_url,
                json={"model": self.embed_model, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts — one request per text (Ollama /api/embeddings)."""
        return [self.embed(t) for t in texts]

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def _ensure_collection(self) -> None:
        """Create the Qdrant collection if it does not already exist."""
        existing = {c.name for c in self._client.get_collections().collections}
        if self.collection not in existing:
            self._client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=_DEFAULT_VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection: %s", self.collection)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> int:
        """Embed and upsert a list of chunk dicts into Qdrant.

        Each chunk dict must have:
            text        str   — content to embed
            document_id str   — parent document UUID
            filename    str   — original filename
            entity_ids  list  — extracted entity IDs
            metadata    dict  — arbitrary extra fields

        Returns the number of chunks upserted.
        """
        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        vectors = self.embed_batch(texts)

        points = [
            PointStruct(
                id=str(uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"{c['document_id']}:{c.get('metadata', {}).get('chunk_index', i)}",
                )),
                vector=vector,
                payload={
                    **c.get("metadata", {}),
                    "text":        c["text"],
                    "document_id": c["document_id"],
                    "filename":    c.get("filename", ""),
                    "entity_ids":  c.get("entity_ids", []),
                },
            )
            for i, (c, vector) in enumerate(zip(chunks, vectors))
        ]

        self._client.upsert(collection_name=self.collection, points=points)
        logger.info("Upserted %d chunks into Qdrant collection '%s'", len(points), self.collection)
        return len(points)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_document_id: str | None = None,
        filter_entity_id: str | None = None,
    ) -> list[SearchResult]:
        """Semantic search over the chunk collection.

        Args:
            query_vector:        Precomputed query embedding.
            top_k:               Number of results to return.
            filter_document_id:  Narrow results to one document.
            filter_entity_id:    Narrow results to chunks containing this entity ID.

        Returns:
            List of SearchResult sorted by cosine similarity descending.
        """
        # Build optional filter
        conditions = []
        if filter_document_id:
            conditions.append(
                FieldCondition(key="document_id", match=MatchValue(value=filter_document_id))
            )
        if filter_entity_id:
            conditions.append(
                FieldCondition(key="entity_ids", match=MatchValue(value=filter_entity_id))
            )
        qdrant_filter = Filter(must=conditions) if conditions else None

        response = self._client.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        hits = response.points

        return [
            SearchResult(
                id=str(hit.id),
                score=hit.score,
                text=hit.payload.get("text", ""),
                document_id=hit.payload.get("document_id", ""),
                filename=hit.payload.get("filename", ""),
                entity_ids=hit.payload.get("entity_ids", []),
                metadata={
                    k: v for k, v in hit.payload.items()
                    if k not in ("text", "document_id", "filename", "entity_ids")
                },
            )
            for hit in hits
        ]

    def count(self) -> int:
        """Return the total number of vectors in the collection."""
        return self._client.count(collection_name=self.collection).count

    def count_document(self, document_id: str) -> int:
        """Return the number of indexed chunks for one PostgreSQL document."""
        result = self._client.count(
            collection_name=self.collection,
            count_filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
            exact=True,
        )
        return result.count


# ── module-level singleton ────────────────────────────────────────────────────
_instance: QdrantVectorClient | None = None


def get_qdrant_client() -> QdrantVectorClient:
    """Return a module-level singleton QdrantVectorClient."""
    global _instance
    if _instance is None:
        _instance = QdrantVectorClient()
    return _instance
