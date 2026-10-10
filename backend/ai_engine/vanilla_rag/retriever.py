"""Vanilla RAG retrieval — semantic search over Qdrant.

Replaces the previous in-memory JSON-backed store with persistent
Qdrant vector search using nomic-embed-text embeddings via Ollama.

Flow:
    query → embed (nomic-embed-text) → Qdrant ANN search
         → rerank (similarity + coverage) → build context → return
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from time import perf_counter
from typing import Any

from ai_engine.embeddings.embedding_model import EmbeddingModel
from ai_engine.vanilla_rag.reranker import rerank_qdrant
from ai_engine.vanilla_rag.scoring import relevance_score
from database.vector.qdrant_client import QdrantVectorClient, SearchResult, get_qdrant_client


@dataclass(frozen=True)
class RetrievalResult:
    query: str
    processed_query: str
    query_embedding: list[float]
    chunks: list[SearchResult]
    retrieved_context: str
    relevance_score: float
    latency_ms: float
    candidates_scanned: int


class VanillaRAGRetriever:
    """Semantic retrieval from Qdrant using nomic-embed-text."""

    def __init__(
        self,
        qdrant: QdrantVectorClient | None = None,
        embedding_model: EmbeddingModel | None = None,
    ) -> None:
        self._qdrant  = qdrant          or get_qdrant_client()
        self.embedding_model = embedding_model or EmbeddingModel()

    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_entity_id: str | None = None,
    ) -> RetrievalResult:
        """Retrieve top-k semantically relevant chunks for a query.

        Args:
            query:             Natural-language query.
            top_k:             Number of results (1–20).
            filter_entity_id:  Optional entity ID filter (e.g. 'REQ-0042').

        Returns:
            RetrievalResult with ranked chunks and formatted context.
        """
        processed = " ".join(query.strip().split())
        if not processed:
            raise ValueError("Query must not be empty")
        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10")

        started_at = perf_counter()

        # Embed
        query_embedding = self.embedding_model.embed(processed)

        # Search Qdrant
        entity_ids = self._extract_entity_ids(processed)
        raw_results = self._qdrant.search(
            query_vector=query_embedding,
            top_k=min(20, max(top_k * 4, 10)),   # over-fetch then rerank
            filter_entity_id=filter_entity_id,
        )

        exact_results: list[SearchResult] = []
        for entity_id in entity_ids:
            exact_results.extend(self._qdrant.search(
                query_vector=query_embedding, top_k=20, filter_entity_id=entity_id
            ))
        candidates = {result.id: result for result in [*raw_results, *exact_results]}

        # Rerank using similarity + query coverage
        ranked = rerank_qdrant(processed, list(candidates.values()), boost_entity_ids=entity_ids)
        if entity_ids:
            matched = [item for item in ranked if set(item.entity_ids).intersection(entity_ids)]
            unrelated = [item for item in ranked if item not in matched]
            ranked = (matched + unrelated)[: max(top_k, min(10, len(matched)))]
        else:
            ranked = ranked[:top_k]

        # Build context string
        context = self._build_context(ranked)

        top_score = ranked[0].score if ranked else 0.0
        latency_ms = (perf_counter() - started_at) * 1000

        return RetrievalResult(
            query=query,
            processed_query=processed,
            query_embedding=query_embedding,
            chunks=ranked,
            retrieved_context=context,
            relevance_score=top_score,
            latency_ms=latency_ms,
            candidates_scanned=self._qdrant.count(),
        )

    @staticmethod
    def _extract_entity_ids(query: str) -> list[str]:
        return sorted({match.upper() for match in re.findall(
            r"\b(?:BUG|REQ|TC|FAIL|EXEC|RUN|ENV|REL)-\d{3,6}\b", query, re.IGNORECASE
        )})

    # ------------------------------------------------------------------

    @staticmethod
    def _build_context(results: list[SearchResult]) -> str:
        sections = []
        for result in results:
            entity_str = ", ".join(result.entity_ids) if result.entity_ids else "—"
            sections.append(
                f"[{result.filename} | score={result.score:.3f} | entities={entity_str}]\n"
                f"{result.text}"
            )
        return "\n\n".join(sections)
