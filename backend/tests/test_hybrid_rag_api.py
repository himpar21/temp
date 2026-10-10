"""Tests for the unified adaptive RAG API handler."""

import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from ai_engine.hybrid_rag.planner import HybridRAGPlanner
from api.dependencies import get_current_user
from api.routes.hybrid_rag import _execute_pipeline
from schemas.request.query_schema import HybridRAGPlanQuery


class UnifiedHybridRAGHandlerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.planner = HybridRAGPlanner()

    def test_default_threshold_routes_from_reported_score(self) -> None:
        response = _execute_pipeline(
            HybridRAGPlanQuery(
                query="Why do Galaxy Buds disconnect after screen lock?",
                top_k=3,
            ),
            self.planner,
        )

        expected = (
            "vanilla_rag"
            if response.decision.vanilla_relevance_score >= response.decision.threshold
            else "graph_rag"
        )
        self.assertEqual(expected, response.decision.selected_source.value)
        self.assertEqual(0.85, response.decision.threshold)
        self.assertTrue(response.selected_context)

    def test_graph_route_returns_complete_trace_and_graph_result(self) -> None:
        response = _execute_pipeline(
            HybridRAGPlanQuery(
                query="Which feature is most unstable in SmartThings?",
                top_k=5,
                threshold=0.99,
            ),
            self.planner,
        )

        self.assertEqual("graph_rag", response.decision.selected_source.value)
        self.assertIsNotNone(response.graph_result)
        self.assertEqual("completed", response.pipeline_trace[3].status)
        self.assertEqual(5, len(response.pipeline_trace))
        self.assertIn("Automation", response.selected_context)

    def test_graph_route_respects_requested_top_k(self) -> None:
        response = _execute_pipeline(
            HybridRAGPlanQuery(
                query="Which feature is most unstable in SmartThings?",
                top_k=1,
                threshold=0.99,
            ),
            self.planner,
        )

        self.assertIsNotNone(response.graph_result)
        self.assertEqual(1, len(response.graph_result.paths))

    def test_graph_context_is_forwarded_to_llm_generation(self) -> None:
        calls: list[dict[str, str | None]] = []

        class FakeGenerator:
            def generate(self, query: str, **contexts: str | None) -> SimpleNamespace:
                calls.append({"query": query, **contexts})
                return SimpleNamespace(answer="Grounded graph answer")

        response = _execute_pipeline(
            HybridRAGPlanQuery(
                query="Which feature is most unstable in SmartThings?",
                top_k=3,
                threshold=0.99,
            ),
            self.planner,
            FakeGenerator(),  # type: ignore[arg-type]
        )

        self.assertEqual("Grounded graph answer", response.answer)
        self.assertIn("Graph RAG", calls[0]["graph_context"] or "")
        self.assertIsNone(calls[0]["vanilla_context"])
        self.assertEqual("llm_generation", response.pipeline_trace[-1].stage)


class UnifiedHybridRAGValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app.dependency_overrides[get_current_user] = lambda: object()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.pop(get_current_user, None)

    def test_whitespace_and_punctuation_queries_are_rejected(self) -> None:
        for query in ("   ", "???"):
            with self.subTest(query=query):
                response = self.client.post(
                    "/api/v1/hybrid-rag/query",
                    json={"query": query, "top_k": 3, "threshold": 0.3},
                )
                self.assertEqual(422, response.status_code)

    def test_invalid_routing_parameters_are_rejected(self) -> None:
        invalid_bodies = (
            {"query": "valid query", "top_k": 0, "threshold": 0.3},
            {"query": "valid query", "top_k": 11, "threshold": 0.3},
        )
        for body in invalid_bodies:
            with self.subTest(body=body):
                response = self.client.post("/api/v1/hybrid-rag/query", json=body)
                self.assertEqual(422, response.status_code)

    def test_request_threshold_does_not_override_server_configuration(self) -> None:
        response = self.client.post(
            "/api/v1/hybrid-rag/query",
            json={"query": "valid query", "top_k": 3, "threshold": 0.1},
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0.85, response.json()["decision"]["threshold"])


if __name__ == "__main__":
    unittest.main()
