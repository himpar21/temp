"""Domain types and an in-memory store for the test-management graph."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class NodeType(str, Enum):
    APPLICATION = "application"
    PROJECT = "project"
    COMPONENT = "component"
    FEATURE = "feature"
    REQUIREMENT = "requirement"
    TEST_CASE = "test_case"
    EXECUTION = "execution"
    FAILURE = "failure"
    DEFECT = "defect"
    EXECUTION_REPORT = "execution_report"
    DOCUMENT = "document"


class RelationshipType(str, Enum):
    HAS_COMPONENT = "has_component"
    HAS_FEATURE = "has_feature"
    DEFINES = "defines"
    IMPLEMENTS = "implements"
    VALIDATES = "validates"
    HAS_EXECUTION = "has_execution"
    DETECTS = "detects"
    PRODUCES = "produces"
    LINKED_TO = "linked_to"
    RELATED_TO = "related_to"


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: NodeType
    label: str
    properties: dict[str, Any] = field(default_factory=dict)
    aliases: tuple[str, ...] = ()

    @property
    def searchable_text(self) -> str:
        values = " ".join(str(value) for value in self.properties.values())
        return " ".join((self.label, *self.aliases, values))


@dataclass(frozen=True)
class GraphEdge:
    source_id: str
    target_id: str
    relationship: RelationshipType
    strength: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("Relationship strength must be between 0 and 1")


class KnowledgeGraph:
    """Small bidirectionally traversable graph with directed edge semantics."""

    def __init__(self, nodes: Iterable[GraphNode], edges: Iterable[GraphEdge]) -> None:
        self.nodes = {node.node_id: node for node in nodes}
        if not self.nodes:
            raise ValueError("Knowledge graph must contain at least one node")

        self.edges = list(edges)
        self._adjacency: dict[str, list[tuple[GraphEdge, str]]] = defaultdict(list)
        for edge in self.edges:
            if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
                raise ValueError(
                    f"Edge references an unknown node: {edge.source_id} -> {edge.target_id}"
                )
            self._adjacency[edge.source_id].append((edge, edge.target_id))
            self._adjacency[edge.target_id].append((edge, edge.source_id))

    def neighbors(self, node_id: str) -> list[tuple[GraphEdge, GraphNode]]:
        return [
            (edge, self.nodes[neighbor_id])
            for edge, neighbor_id in self._adjacency.get(node_id, [])
        ]

    def degree(self, node_id: str) -> int:
        return len(self._adjacency.get(node_id, []))

    def nodes_of_type(self, node_type: NodeType) -> list[GraphNode]:
        return [node for node in self.nodes.values() if node.node_type is node_type]

    def merged_with(self, *others: "KnowledgeGraph") -> "KnowledgeGraph":
        """Return a deterministic union, preferring newer node properties."""

        nodes = dict(self.nodes)
        edges = {
            (edge.source_id, edge.target_id, edge.relationship): edge
            for edge in self.edges
        }
        for graph in others:
            for node_id, incoming in graph.nodes.items():
                existing = nodes.get(node_id)
                if existing is None:
                    nodes[node_id] = incoming
                    continue
                nodes[node_id] = GraphNode(
                    node_id=node_id,
                    node_type=incoming.node_type,
                    label=incoming.label or existing.label,
                    properties={**existing.properties, **incoming.properties},
                    aliases=tuple(dict.fromkeys((*existing.aliases, *incoming.aliases))),
                )
            for edge in graph.edges:
                edges[(edge.source_id, edge.target_id, edge.relationship)] = edge
        return KnowledgeGraph(nodes.values(), edges.values())
