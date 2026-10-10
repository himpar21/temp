"""Map extracted mentions to knowledge-graph nodes."""

from __future__ import annotations

from dataclasses import dataclass

from ai_engine.embeddings.embedding_model import tokenize
from ai_engine.graph_rag.entity_extractor import ExtractedEntity, ProcessedGraphQuery
from database.graph.graph_schema import GraphNode, KnowledgeGraph


@dataclass(frozen=True)
class LinkedEntity:
    mention: str
    node: GraphNode
    confidence: float


class EntityLinker:
    def link(
        self,
        entities: list[ExtractedEntity],
        query: ProcessedGraphQuery,
        graph: KnowledgeGraph,
        limit: int = 5,
    ) -> list[LinkedEntity]:
        linked: dict[str, LinkedEntity] = {}

        for entity in entities:
            mention = entity.mention.lower()
            mention_tokens = set(tokenize(mention))
            candidates: list[tuple[float, GraphNode]] = []
            for node in graph.nodes.values():
                if entity.expected_type and node.node_type is not entity.expected_type:
                    continue
                names = (node.label, *node.aliases)
                exact = any(mention == name.lower() for name in names)
                artifact_match = mention == node.label.lower()
                node_tokens = set(tokenize(node.searchable_text))
                overlap = len(mention_tokens & node_tokens) / max(1, len(mention_tokens))
                score = 1.0 if exact or artifact_match else 0.75 * overlap
                if score:
                    candidates.append((score * entity.confidence, node))
            if candidates:
                score, node = max(candidates, key=lambda item: item[0])
                current = linked.get(node.node_id)
                if current is None or score > current.confidence:
                    linked[node.node_id] = LinkedEntity(entity.mention, node, score)

        # Queries without a named entity still get lexical seed nodes.
        if not linked:
            query_tokens = set(query.keywords)
            candidates = []
            for node in graph.nodes.values():
                node_tokens = set(tokenize(node.searchable_text))
                score = len(query_tokens & node_tokens) / max(1, len(query_tokens))
                if score:
                    candidates.append((score, node))
            for score, node in sorted(candidates, key=lambda item: item[0], reverse=True)[:limit]:
                linked[node.node_id] = LinkedEntity(node.label, node, min(0.9, score))

        return sorted(linked.values(), key=lambda item: item.confidence, reverse=True)[:limit]

