"""Build a knowledge graph from the local test-management artifact corpus."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from database.graph.graph_schema import (
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    NodeType,
    RelationshipType,
)


DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "samsung_testing_artifacts.json"
)

_TYPE_MAP = {
    "requirement": NodeType.REQUIREMENT,
    "test_case": NodeType.TEST_CASE,
    "defect": NodeType.DEFECT,
    "execution_log": NodeType.EXECUTION_REPORT,
    "test_report": NodeType.EXECUTION_REPORT,
}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


class GraphBuilder:
    """Turn artifact metadata into projects, features and evidence relations."""

    def __init__(self, dataset_path: Path | str = DEFAULT_DATASET_PATH) -> None:
        self.dataset_path = Path(dataset_path)

    def _load_records(self) -> list[dict[str, Any]]:
        with self.dataset_path.open(encoding="utf-8") as dataset_file:
            records = json.load(dataset_file)
        if not isinstance(records, list) or not records:
            raise ValueError("Graph source dataset must be a non-empty list")
        return records

    def build(self) -> KnowledgeGraph:
        records = self._load_records()
        nodes: dict[str, GraphNode] = {}
        edges: dict[tuple[str, str, RelationshipType], GraphEdge] = {}
        artifacts_by_feature: dict[str, list[GraphNode]] = {}

        def add_edge(edge: GraphEdge) -> None:
            edges[(edge.source_id, edge.target_id, edge.relationship)] = edge

        for record in records:
            metadata = record.get("metadata", {})
            project = str(metadata.get("project", "Unassigned Project"))
            feature = str(metadata.get("module", "General"))
            project_id = f"project:{_slug(project)}"
            feature_id = f"feature:{_slug(project)}:{_slug(feature)}"
            artifact_id = str(record["artifact_id"])
            artifact_node_id = f"artifact:{artifact_id.lower()}"
            node_type = _TYPE_MAP.get(record.get("artifact_type"), NodeType.EXECUTION_REPORT)

            nodes.setdefault(
                project_id,
                GraphNode(project_id, NodeType.PROJECT, project, {"project": project}),
            )
            nodes.setdefault(
                feature_id,
                GraphNode(
                    feature_id,
                    NodeType.FEATURE,
                    feature,
                    {"project": project, "module": feature},
                ),
            )
            artifact = GraphNode(
                artifact_node_id,
                node_type,
                artifact_id,
                {
                    "title": record.get("title", ""),
                    "content": record.get("content", ""),
                    **metadata,
                },
                aliases=(str(record.get("title", "")),),
            )
            nodes[artifact_node_id] = artifact
            artifacts_by_feature.setdefault(feature_id, []).append(artifact)

            add_edge(
                GraphEdge(project_id, feature_id, RelationshipType.HAS_FEATURE, 1.0)
            )
        # Connect lifecycle evidence within a feature. These links enable paths such
        # as Project -> Feature -> Requirement -> Test Case -> Defect.
        for feature_id, artifacts in artifacts_by_feature.items():
            by_type = {
                node_type: [node for node in artifacts if node.node_type is node_type]
                for node_type in NodeType
            }
            # Start at the earliest lifecycle stage available so complete datasets
            # produce meaningful multi-hop traceability rather than shortcuts.
            if by_type[NodeType.REQUIREMENT]:
                roots = (by_type[NodeType.REQUIREMENT], RelationshipType.DEFINES)
            elif by_type[NodeType.TEST_CASE]:
                roots = (by_type[NodeType.TEST_CASE], RelationshipType.VALIDATES)
            elif by_type[NodeType.DEFECT]:
                roots = (by_type[NodeType.DEFECT], RelationshipType.DETECTS)
            else:
                roots = (by_type[NodeType.EXECUTION_REPORT], RelationshipType.PRODUCES)
            for root in roots[0]:
                add_edge(GraphEdge(feature_id, root.node_id, roots[1], 0.9))

            for requirement in by_type[NodeType.REQUIREMENT]:
                for test_case in by_type[NodeType.TEST_CASE]:
                    add_edge(
                        GraphEdge(
                            requirement.node_id,
                            test_case.node_id,
                            RelationshipType.IMPLEMENTS,
                            0.92,
                        )
                    )
                if not by_type[NodeType.TEST_CASE]:
                    for defect in by_type[NodeType.DEFECT]:
                        add_edge(
                            GraphEdge(
                                requirement.node_id,
                                defect.node_id,
                                RelationshipType.RELATED_TO,
                                0.82,
                            )
                        )
            for test_case in by_type[NodeType.TEST_CASE]:
                for defect in by_type[NodeType.DEFECT]:
                    add_edge(
                        GraphEdge(
                            test_case.node_id,
                            defect.node_id,
                            RelationshipType.DETECTS,
                            0.95,
                        )
                    )
                for report in by_type[NodeType.EXECUTION_REPORT]:
                    add_edge(
                        GraphEdge(
                            test_case.node_id,
                            report.node_id,
                            RelationshipType.PRODUCES,
                            0.88,
                        )
                    )
            if not by_type[NodeType.TEST_CASE]:
                for defect in by_type[NodeType.DEFECT]:
                    for report in by_type[NodeType.EXECUTION_REPORT]:
                        add_edge(
                            GraphEdge(
                                defect.node_id,
                                report.node_id,
                                RelationshipType.RELATED_TO,
                                0.85,
                            )
                        )
            for defect in by_type[NodeType.DEFECT]:
                for report in by_type[NodeType.EXECUTION_REPORT]:
                    add_edge(
                        GraphEdge(
                            defect.node_id,
                            report.node_id,
                            RelationshipType.RELATED_TO,
                            0.85,
                        )
                    )

        return KnowledgeGraph(nodes.values(), edges.values())

