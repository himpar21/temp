"""Tests for Hybrid RAG threshold evaluation, routing, and serialization."""

import unittest
from dataclasses import replace
from types import SimpleNamespace

from ai_engine.hybrid_rag.planner import HybridRAGPlanner
from ai_engine.hybrid_rag.router import PlannerStatus, RetrievalSource
from ai_engine.hybrid_rag.threshold import evaluate_relevance
from ai_engine.vanilla_rag.retriever import RetrievalResult
from api.routes.hybrid_rag import _serialize_chunks
from database.vector.qdrant_client import SearchResult


RESULT = SearchResult(
    id="point-1", score=0.81,
    text="Release validation passed on the staging environment.",
    document_id="document-1", filename="release-notes.md",
    entity_ids=["REL-006"],
    metadata={"document_type": "release_note", "section": "Validation"},
)


class FakeRetriever:
    def __init__(self, score: float) -> None:
        self.score = score

    def retrieve(self, query: str, top_k: int) -> RetrievalResult:
        result = replace(RESULT, score=self.score)
        return RetrievalResult(
            query=query, processed_query=query.strip(), query_embedding=[1.0, 0.0],
            chunks=[result], retrieved_context=result.text, relevance_score=self.score,
            latency_ms=1.0, candidates_scanned=1,
        )


class ThresholdEvaluationTests(unittest.TestCase):
    def test_score_equal_to_threshold_selects_vanilla_rag(self) -> None:
        self.assertTrue(evaluate_relevance(score=0.4, threshold=0.4).threshold_met)

    def test_invalid_threshold_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            evaluate_relevance(score=0.4, threshold=1.1)


class HybridRAGPlannerTests(unittest.TestCase):
    def test_high_relevance_selects_vanilla_context(self) -> None:
        plan = HybridRAGPlanner(FakeRetriever(0.81)).plan("release validation", 3, 0.4)

        self.assertEqual(RetrievalSource.VANILLA_RAG, plan.selected_source)
        self.assertEqual(PlannerStatus.CONTEXT_SELECTED, plan.status)
        self.assertEqual("augmentation_response_generation", plan.next_stage)
        self.assertEqual(plan.vanilla_result.chunks, plan.selected_chunks)

    def test_low_relevance_selects_graph_rag_context(self) -> None:
        plan = HybridRAGPlanner(FakeRetriever(0.2)).plan(
            "Which feature is most unstable in SmartThings?",
            top_k=3,
            threshold=0.99,
        )

        self.assertEqual(RetrievalSource.GRAPH_RAG, plan.selected_source)
        self.assertEqual(PlannerStatus.GRAPH_CONTEXT_SELECTED, plan.status)
        self.assertEqual("augmentation_response_generation", plan.next_stage)
        self.assertIsNotNone(plan.selected_context)
        self.assertIsNotNone(plan.graph_result)
        self.assertIn("Graph RAG", plan.selected_context)
        self.assertEqual([], plan.selected_chunks)

    def test_qdrant_result_serialization_uses_current_fields(self) -> None:
        serialized = _serialize_chunks([RESULT])[0]

        self.assertEqual("point-1", serialized.chunk_id)
        self.assertEqual("document-1", serialized.artifact_id)
        self.assertEqual("release_note", serialized.artifact_type)
        self.assertEqual("release-notes.md", serialized.title)
        self.assertEqual(0.81, serialized.similarity_score)

    def test_no_graph_evidence_does_not_select_placeholder_context(self) -> None:
        plan = HybridRAGPlanner(FakeRetriever(0.2)).plan(
            "unknown quantum flux banana",
            top_k=3,
            threshold=1.0,
        )

        self.assertEqual(RetrievalSource.GRAPH_RAG, plan.selected_source)
        self.assertEqual(PlannerStatus.NO_CONTEXT_FOUND, plan.status)
        self.assertEqual("no_context", plan.next_stage)
        self.assertIsNone(plan.selected_context)
        self.assertIsNotNone(plan.graph_result)
        self.assertEqual([], plan.graph_result.paths)

    def test_usable_vanilla_evidence_is_kept_when_graph_has_no_paths(self) -> None:
        class EmptyGraphRetriever:
            def retrieve(self, query: str, top_k: int) -> SimpleNamespace:
                return SimpleNamespace(paths=[])

        plan = HybridRAGPlanner(
            FakeRetriever(0.55),
            EmptyGraphRetriever(),  # type: ignore[arg-type]
        ).plan("Give complete details of DR-BUG-0026", 3, 0.7)

        self.assertEqual(RetrievalSource.VANILLA_RAG, plan.selected_source)
        self.assertEqual(PlannerStatus.CONTEXT_SELECTED, plan.status)
        self.assertIsNotNone(plan.selected_context)
        self.assertEqual(1, len(plan.selected_chunks))
        self.assertIn("safe fallback", plan.decision_reason)

    def test_usable_vanilla_evidence_is_kept_when_graph_fails(self) -> None:
        class FailingGraphRetriever:
            def retrieve(self, query: str, top_k: int) -> SimpleNamespace:
                raise TimeoutError("graph traversal budget exceeded")

        plan = HybridRAGPlanner(
            FakeRetriever(0.55),
            FailingGraphRetriever(),  # type: ignore[arg-type]
        ).plan("Give complete details of BUG-0518", 3, 0.85)

        self.assertEqual(RetrievalSource.VANILLA_RAG, plan.selected_source)
        self.assertEqual(PlannerStatus.CONTEXT_SELECTED, plan.status)
        self.assertIn("Graph RAG retrieval failed", plan.decision_reason)

    def test_score_equal_to_threshold_selects_vanilla_pipeline(self) -> None:
        plan = HybridRAGPlanner(FakeRetriever(0.4)).plan(
            "threshold equality", top_k=3, threshold=0.4
        )

        self.assertEqual(RetrievalSource.VANILLA_RAG, plan.selected_source)


if __name__ == "__main__":
    unittest.main()
