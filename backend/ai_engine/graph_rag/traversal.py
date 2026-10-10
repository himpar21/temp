"""Bounded multi-hop traversal over the knowledge graph."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import os
from time import perf_counter

from ai_engine.graph_rag.entity_linker import LinkedEntity
from database.graph.graph_schema import GraphEdge, GraphNode, KnowledgeGraph


@dataclass(frozen=True)
class TraversalPath:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]

    @property
    def hops(self) -> int:
        return len(self.edges)


class GraphTraverser:
    def traverse(
        self,
        graph: KnowledgeGraph,
        seeds: list[LinkedEntity],
        max_hops: int = 4,
        max_paths: int | None = None,
        max_expansions: int | None = None,
        time_budget_seconds: float | None = None,
    ) -> list[TraversalPath]:
        if not 1 <= max_hops <= 6:
            raise ValueError("max_hops must be between 1 and 6")

        path_limit = (
            int(os.getenv("GRAPH_RAG_MAX_PATHS", "2000"))
            if max_paths is None
            else max_paths
        )
        expansion_limit = (
            int(os.getenv("GRAPH_RAG_MAX_EXPANSIONS", "10000"))
            if max_expansions is None
            else max_expansions
        )
        time_budget = (
            float(os.getenv("GRAPH_RAG_TIME_BUDGET_SECONDS", "2.0"))
            if time_budget_seconds is None
            else time_budget_seconds
        )
        if path_limit < 1 or expansion_limit < 1 or time_budget <= 0:
            raise ValueError("Graph traversal limits must be positive")

        paths: list[TraversalPath] = []
        seen_signatures: set[tuple[str, ...]] = set()
        scheduled = 0
        deadline = perf_counter() + time_budget
        for seed in seeds:
            if len(paths) >= path_limit or scheduled >= expansion_limit:
                break
            queue = deque([((seed.node,), tuple())])
            scheduled += 1
            while queue and len(paths) < path_limit and perf_counter() < deadline:
                nodes, edges = queue.popleft()
                if edges:
                    signature = tuple(node.node_id for node in nodes)
                    if signature not in seen_signatures:
                        seen_signatures.add(signature)
                        paths.append(TraversalPath(nodes, edges))
                if len(edges) == max_hops:
                    continue
                visited = {node.node_id for node in nodes}
                for edge, neighbor in graph.neighbors(nodes[-1].node_id):
                    if scheduled >= expansion_limit or perf_counter() >= deadline:
                        break
                    if neighbor.node_id not in visited:
                        queue.append((nodes + (neighbor,), edges + (edge,)))
                        scheduled += 1
        return paths

