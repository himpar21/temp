"""Relationship-aware path ranking and graph confidence scoring."""

from __future__ import annotations

from dataclasses import dataclass

from ai_engine.embeddings.embedding_model import tokenize
from ai_engine.graph_rag.entity_extractor import ProcessedGraphQuery
from ai_engine.graph_rag.traversal import TraversalPath
from database.graph.graph_schema import KnowledgeGraph, NodeType


_MAX_CONTENT_CHARS_FOR_RANKING = 3000


def _node_terms(node: object) -> set[str]:
    """Return bounded searchable terms without repeatedly tokenizing large sources."""

    label = str(getattr(node, "label", ""))
    aliases = " ".join(str(value) for value in getattr(node, "aliases", ()))
    properties = getattr(node, "properties", {})
    metadata = " ".join(
        str(value)
        for key, value in properties.items()
        if key not in {"content", "source_document_id", "_aliases"}
    )
    content = str(properties.get("content", ""))[:_MAX_CONTENT_CHARS_FOR_RANKING]
    return set(tokenize(" ".join((label, aliases, metadata, content))))


@dataclass(frozen=True)
class RankedPath:
    path: TraversalPath
    score: float
    relationship_strength: float


def _instability_boost(path: TraversalPath, intent: str) -> float:
    if intent != "instability_analysis":
        return 0.0
    terminal = path.nodes[-1]
    status = str(terminal.properties.get("status", "")).lower()
    if terminal.node_type is NodeType.DEFECT:
        return 0.18 if status in {"open", "in_progress"} else 0.10
    if terminal.node_type is NodeType.EXECUTION_REPORT:
        return 0.14 if status in {"failed", "regression"} else 0.06
    return 0.0


def rank_paths(
    paths: list[TraversalPath],
    query: ProcessedGraphQuery,
    graph: KnowledgeGraph,
    top_k: int,
) -> list[RankedPath]:
    query_terms = set(query.keywords)
    ranked: list[RankedPath] = []
    term_cache = {
        node.node_id: _node_terms(node)
        for path in paths
        for node in path.nodes
    }
    for path in paths:
        path_terms: set[str] = set()
        for node in path.nodes:
            path_terms.update(term_cache[node.node_id])
        lexical = len(query_terms & path_terms) / max(1, len(query_terms))
        strength = sum(edge.strength for edge in path.edges) / len(path.edges)
        length_score = 1.0 / path.hops
        degree = graph.degree(path.nodes[-1].node_id)
        importance = min(1.0, degree / 5.0)
        score = (
            0.42 * lexical
            + 0.28 * strength
            + 0.15 * length_score
            + 0.15 * importance
            + _instability_boost(path, query.intent)
        )
        ranked.append(RankedPath(path, min(1.0, score), strength))

    ranked.sort(key=lambda item: (-item.score, item.path.hops))
    return ranked[: min(top_k, len(ranked))]


def graph_confidence(
    ranked_paths: list[RankedPath], linked_entity_count: int
) -> float:
    if not ranked_paths or not linked_entity_count:
        return 0.0
    top_scores = [item.score for item in ranked_paths[:3]]
    evidence_score = sum(top_scores) / len(top_scores)
    entity_factor = min(1.0, 0.7 + 0.1 * linked_entity_count)
    return min(1.0, evidence_score * entity_factor)
