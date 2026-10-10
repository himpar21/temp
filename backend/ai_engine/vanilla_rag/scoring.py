"""Retrieval scoring utilities — used by both Vanilla RAG and Graph RAG."""

from __future__ import annotations

import math
from collections.abc import Sequence

from ai_engine.embeddings.embedding_model import tokenize


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Return cosine similarity for two equal-length vectors."""
    if len(left) != len(right):
        raise ValueError("Vectors must have the same dimension")
    left_norm  = math.sqrt(sum(v * v for v in left))
    right_norm = math.sqrt(sum(v * v for v in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def query_coverage(query: str, document: str) -> float:
    """Fraction of normalised query terms that appear in the document."""
    query_terms = set(tokenize(query))
    if not query_terms:
        return 0.0
    doc_terms = set(tokenize(document))
    return len(query_terms & doc_terms) / len(query_terms)


def relevance_score(similarity: float, coverage: float) -> float:
    """Blend semantic similarity (85%) and keyword coverage (15%)."""
    return (0.85 * max(0.0, min(1.0, similarity))) + \
           (0.15 * max(0.0, min(1.0, coverage)))
