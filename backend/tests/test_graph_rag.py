"""Tests for the complete relationship-aware Graph RAG pipeline."""

import unittest
from types import SimpleNamespace

from ai_engine.graph_rag.graph_retriever import GraphRAGRetriever
from ai_engine.graph_rag.entity_linker import LinkedEntity
from ai_engine.graph_rag.traversal import GraphTraverser
from database.graph.graph_schema import (
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    NodeType,
    RelationshipType,
)
from services.graph_projection_service import GraphProjectionService


class GraphRAGRetrieverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.retriever = GraphRAGRetriever()

    def test_smartthings_instability_query_traverses_lifecycle_graph(self) -> None:
        result = self.retriever.retrieve(
            "Which feature is most unstable in SmartThings?",
            top_k=10,
            max_hops=4,
        )

        self.assertEqual("instability_analysis", result.processed_query.intent)
        self.assertEqual("SmartThings", result.linked_entities[0].node.label)
        self.assertEqual(NodeType.PROJECT, result.linked_entities[0].node.node_type)
        self.assertTrue(result.paths)
        self.assertGreater(result.confidence_score, 0.0)
        self.assertIn("Automation", result.graph_context)
        self.assertIn("DEF-IOT-309", result.graph_context)
        self.assertTrue(
            any(
                [node.node_type for node in ranked.path.nodes]
                == [
                    NodeType.PROJECT,
                    NodeType.FEATURE,
                    NodeType.REQUIREMENT,
                    NodeType.TEST_CASE,
                    NodeType.DEFECT,
                ]
                for ranked in result.paths
            )
        )

    def test_artifact_identifier_is_extracted_and_linked(self) -> None:
        result = self.retriever.retrieve(
            "Show dependencies for DEF-IOT-310", top_k=5, max_hops=3
        )

        self.assertIn("DEF-IOT-310", [item.mention for item in result.extracted_entities])
        self.assertEqual("DEF-IOT-310", result.linked_entities[0].node.label)
        self.assertIn("$seed_ids", result.generated_query)

    def test_spaced_artifact_identifier_is_normalized_and_linked(self) -> None:
        result = self.retriever.retrieve(
            "What is defect bug 0310 about?", top_k=5, max_hops=3
        )

        self.assertIn("BUG-0310", [item.mention for item in result.extracted_entities])

    def test_invalid_limits_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "top_k"):
            self.retriever.retrieve("SmartThings failures", top_k=0)
        with self.assertRaisesRegex(ValueError, "max_hops"):
            self.retriever.retrieve("SmartThings failures", max_hops=7)

    def test_uploaded_defect_is_projected_into_a_queryable_traceability_path(self) -> None:
        document = SimpleNamespace(
            id="document-26",
            logical_document_id="DR-BUG-0026",
            filename="DR-BUG-0026.md",
            document_type="defect_report",
            document_metadata={"document_type": "defect_report"},
            entity_ids=[
                "DR-BUG-0026",
                "REQ-0345",
                "TC-0660",
                "EXEC-02810",
                "FAIL-0546",
            ],
            text="""# Defect Report DR-BUG-0026
Application: XRPlatform
Component: UI Layer
Severity: Major
Priority: Critical
Status: IN_PROGRESS
Requirement: REQ-0345
Test Case: TC-0660
Execution: EXEC-02810
Failure: FAIL-0546
Root Cause: Database migration updated the user_sessions index incorrectly.
""",
        )
        graph = GraphProjectionService(session=None).project(document)  # type: ignore[arg-type]
        retriever = GraphRAGRetriever(dynamic_loader=lambda: graph)

        result = retriever.retrieve(
            "Give complete details of DR-BUG-0026", top_k=10, max_hops=4
        )

        self.assertEqual("DR-BUG-0026", result.linked_entities[0].node.label)
        self.assertTrue(result.paths)
        self.assertTrue(
            any(
                {"DR-BUG-0026", "REQ-0345", "TC-0660", "FAIL-0546"}
                <= {node.label for node in ranked.path.nodes}
                for ranked in result.paths
            )
        )
        self.assertIn("Database migration", result.graph_context)

    def test_structured_upload_relationships_are_scoped_to_each_row(self) -> None:
        document = SimpleNamespace(
            id="structured-document",
            logical_document_id="cases",
            filename="cases.json",
            document_type="structured_json",
            document_metadata={"document_type": "structured_json"},
            entity_ids=["REQ-0001", "REQ-0002", "TC-0001", "TC-0002"],
            text=(
                '{"requirement_id":"REQ-0001","test_case_id":"TC-0001"}\n'
                '{"requirement_id":"REQ-0002","test_case_id":"TC-0002"}'
            ),
        )

        graph = GraphProjectionService(session=None).project(document)  # type: ignore[arg-type]
        implements = {
            (edge.source_id, edge.target_id)
            for edge in graph.edges
            if edge.relationship is RelationshipType.IMPLEMENTS
        }

        self.assertEqual(
            {
                ("entity:req-0001", "entity:tc-0001"),
                ("entity:req-0002", "entity:tc-0002"),
            },
            implements,
        )

    def test_dense_graph_traversal_respects_path_and_expansion_limits(self) -> None:
        nodes = [GraphNode("seed", NodeType.DEFECT, "BUG-0518")]
        nodes.extend(
            GraphNode(f"node-{index}", NodeType.TEST_CASE, f"TC-{index:04d}")
            for index in range(100)
        )
        edges = [
            GraphEdge("seed", node.node_id, RelationshipType.RELATED_TO)
            for node in nodes[1:]
        ]
        graph = KnowledgeGraph(nodes, edges)
        seed = LinkedEntity("BUG-0518", nodes[0], 1.0)

        paths = GraphTraverser().traverse(
            graph,
            [seed],
            max_hops=4,
            max_paths=10,
            max_expansions=20,
            time_budget_seconds=1.0,
        )

        self.assertLessEqual(len(paths), 10)
        self.assertTrue(paths)


if __name__ == "__main__":
    unittest.main()
