"""Rerank Qdrant search results using similarity and query coverage."""

from __future__ import annotations

from dataclasses import replace

from ai_engine.vanilla_rag.scoring import query_coverage, relevance_score
from database.vector.qdrant_client import SearchResult


def rerank_qdrant(query: str, candidates: list[SearchResult], boost_entity_ids: list[str] | None = None) -> list[SearchResult]:
    """Re-score and re-sort Qdrant results using coverage-blended relevance.

    Qdrant already returns cosine similarity scores. We blend those with
    query-term coverage for a final relevance score.
    """
    scored = []
    for candidate in candidates:
        coverage = query_coverage(query, candidate.text)
        blended  = relevance_score(candidate.score, coverage)
        if boost_entity_ids and set(candidate.entity_ids).intersection(boost_entity_ids):
            blended = min(1.0, blended + 0.25)
        # Replace the score field with the blended relevance score
        scored.append(replace(candidate, score=blended))
    return sorted(scored, key=lambda r: r.score, reverse=True)
