"""Embedding model using Ollama nomic-embed-text.

Replaces the previous feature-hashing demo with real semantic embeddings
from the locally-running Ollama nomic-embed-text model (274 MB).

No external API, no API key — fully local via the Ollama HTTP endpoint.

Environment variables:
    OLLAMA_BASE_URL    — Ollama server URL       (default: http://localhost:11434)
    OLLAMA_EMBED_MODEL — embedding model name    (default: nomic-embed-text)
    OLLAMA_TIMEOUT     — request timeout seconds (default: 120)

nomic-embed-text produces 768-dimensional L2-normalized vectors.
It is specifically trained for retrieval tasks and significantly
outperforms feature-hashing for semantic search.
"""

from __future__ import annotations

import os
from collections.abc import Iterable

import httpx

_DEFAULT_BASE_URL    = "http://localhost:11434"
_DEFAULT_EMBED_MODEL = "nomic-embed-text"
_DEFAULT_TIMEOUT     = 120
_VECTOR_DIM          = 768   # nomic-embed-text output dimension


def tokenize(text: str) -> list[str]:
    """Simple whitespace tokenizer kept for backwards-compat with scoring utils."""
    import re
    _STOP = {
        "a","an","and","are","as","at","be","by","for","from",
        "in","is","it","of","on","or","the","to","with",
    }
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in _STOP and len(t) > 1]


class EmbeddingModel:
    """Semantic embedding via Ollama nomic-embed-text."""

    def __init__(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        raw_base      = base_url or os.getenv("OLLAMA_BASE_URL", _DEFAULT_BASE_URL)
        self._url     = raw_base.rstrip("/") + "/api/embeddings"
        self.name     = model   or os.getenv("OLLAMA_EMBED_MODEL", _DEFAULT_EMBED_MODEL)
        self._timeout = timeout or int(os.getenv("OLLAMA_TIMEOUT", str(_DEFAULT_TIMEOUT)))
        self.dimension = _VECTOR_DIM

    def embed(self, text: str) -> list[float]:
        """Return a 768-dim embedding vector for a single text."""
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                self._url,
                json={"model": self.name, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]

    def embed_many(self, texts: Iterable[str]) -> list[list[float]]:
        """Embed multiple texts sequentially."""
        return [self.embed(t) for t in texts]
