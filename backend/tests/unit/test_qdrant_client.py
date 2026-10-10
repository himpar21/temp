"""Compatibility tests for the qdrant-client 1.19 API."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from database.vector.qdrant_client import QdrantVectorClient


class QdrantVectorClientTests(unittest.TestCase):
    def test_search_uses_query_points_and_maps_payload(self) -> None:
        wrapper = object.__new__(QdrantVectorClient)
        wrapper.collection = "chunks"
        wrapper._client = Mock()
        wrapper._client.query_points.return_value = SimpleNamespace(points=[SimpleNamespace(
            id="point-1", score=0.88,
            payload={
                "text": "stored text", "document_id": "doc-1", "filename": "sample.md",
                "entity_ids": ["REL-1"], "document_type": "release_note",
            },
        )])

        results = wrapper.search([0.1, 0.2], top_k=3, filter_document_id="doc-1")

        self.assertEqual("point-1", results[0].id)
        self.assertEqual("doc-1", results[0].document_id)
        self.assertEqual("release_note", results[0].metadata["document_type"])
        kwargs = wrapper._client.query_points.call_args.kwargs
        self.assertEqual([0.1, 0.2], kwargs["query"])
        self.assertEqual(3, kwargs["limit"])


if __name__ == "__main__":
    unittest.main()
