"""Unit tests for the Qdrant-backed Vanilla RAG retrieval flow."""

import unittest

from ai_engine.vanilla_rag.retriever import VanillaRAGRetriever
from database.vector.qdrant_client import SearchResult


class FakeEmbeddingModel:
    name = "fake-embedding"
    dimension = 768

    def __init__(self) -> None:
        self.calls: list[str] = []

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        return [1.0] + [0.0] * 767


class FakeQdrant:
    def __init__(self) -> None:
        self.last_vector: list[float] | None = None
        self.last_top_k: int | None = None
        self.results = [
            SearchResult(
                id="chunk-battery", score=0.92,
                text="Overnight battery drain occurs while background sync remains active.",
                document_id="doc-battery", filename="battery-report.md",
                entity_ids=["REPORT-BATT-088"], metadata={"document_type": "report"},
            ),
            SearchResult(
                id="chunk-camera", score=0.75,
                text="Camera portrait mode can crash after rapid rotation.",
                document_id="doc-camera", filename="camera-log.txt",
                entity_ids=["LOG-CAM-042"], metadata={"document_type": "log"},
            ),
            SearchResult(
                id="chunk-display", score=0.51, text="Display brightness test results.",
                document_id="doc-display", filename="display.csv", entity_ids=[],
                metadata={"document_type": "structured_csv"},
            ),
        ]

    def search(self, query_vector, top_k=5, filter_document_id=None, filter_entity_id=None):
        self.last_vector = query_vector
        self.last_top_k = top_k
        return self.results[:top_k]

    def count(self) -> int:
        return len(self.results)


class VanillaRAGRetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.qdrant = FakeQdrant()
        self.embedding = FakeEmbeddingModel()
        self.retriever = VanillaRAGRetriever(self.qdrant, self.embedding)

    def test_returns_requested_number_of_ranked_chunks(self) -> None:
        result = self.retriever.retrieve("overnight battery drain", top_k=2)

        self.assertEqual(2, len(result.chunks))
        self.assertEqual("doc-battery", result.chunks[0].document_id)
        self.assertGreaterEqual(result.chunks[0].score, result.chunks[1].score)
        self.assertIn("battery-report.md", result.retrieved_context)

    def test_query_is_embedded_once_and_vector_is_reused(self) -> None:
        result = self.retriever.retrieve("  camera   crash  ", top_k=2)

        self.assertEqual(["camera crash"], self.embedding.calls)
        self.assertIs(result.query_embedding, self.qdrant.last_vector)
        self.assertEqual(768, len(result.query_embedding))
        self.assertEqual(4, self.qdrant.last_top_k)

    def test_empty_query_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            self.retriever.retrieve("  ")

    def test_invalid_top_k_is_rejected(self) -> None:
        for value in (0, 11):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "between 1 and 10"):
                self.retriever.retrieve("display test", top_k=value)


if __name__ == "__main__":
    unittest.main()
