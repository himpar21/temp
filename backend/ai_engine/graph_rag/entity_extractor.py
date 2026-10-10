"""Query preprocessing and lightweight domain entity recognition."""

from __future__ import annotations

from dataclasses import dataclass
import re

from ai_engine.embeddings.embedding_model import tokenize
from database.graph.graph_schema import KnowledgeGraph, NodeType
from ingestion.preprocessing import ENTITY_PATTERN


@dataclass(frozen=True)
class ProcessedGraphQuery:
    original: str
    normalized: str
    keywords: tuple[str, ...]
    intent: str


@dataclass(frozen=True)
class ExtractedEntity:
    mention: str
    expected_type: NodeType | None
    confidence: float


class EntityExtractor:
    """Recognize graph labels and test-management identifiers without an LLM."""

    _IDENTIFIER = ENTITY_PATTERN
    _LOOSE_IDENTIFIER = re.compile(
        r"\b(DR[\s_-]*BUG|TP[\s_-]*TS|APP|SOL|REQ|TS|TC|EXEC|FAIL|BUG|DEF|"
        r"REPORT|LOG|RUN|ENV|REL|ENG|STEP)\s*[-_ ]\s*(\d{1,8})\b",
        re.IGNORECASE,
    )

    @staticmethod
    def preprocess(query: str) -> ProcessedGraphQuery:
        normalized = " ".join(query.strip().split())
        if not normalized:
            raise ValueError("Query must not be empty")
        lower = normalized.lower()
        if any(term in lower for term in ("unstable", "failure", "failed", "defect")):
            intent = "instability_analysis"
        elif any(term in lower for term in ("depend", "related", "impact", "connected")):
            intent = "relationship_analysis"
        elif any(term in lower for term in ("requirement", "test case", "coverage")):
            intent = "traceability"
        else:
            intent = "graph_search"
        return ProcessedGraphQuery(
            original=query,
            normalized=normalized,
            keywords=tuple(dict.fromkeys(tokenize(normalized))),
            intent=intent,
        )

    def extract(
        self, query: ProcessedGraphQuery, graph: KnowledgeGraph
    ) -> list[ExtractedEntity]:
        query_lower = query.normalized.lower()
        entities: dict[tuple[str, NodeType | None], ExtractedEntity] = {}

        for identifier in self._IDENTIFIER.findall(query.normalized):
            entity = ExtractedEntity(identifier.upper(), None, 1.0)
            entities[(entity.mention.lower(), None)] = entity

        for prefix, number in self._LOOSE_IDENTIFIER.findall(query.normalized):
            normalized_prefix = re.sub(r"[\s_-]+", "-", prefix.upper())
            mention = f"{normalized_prefix}-{number}"
            entity = ExtractedEntity(mention, None, 1.0)
            entities[(entity.mention.lower(), None)] = entity

        # Longest labels first prevents a short alias from hiding a specific match.
        for node in sorted(graph.nodes.values(), key=lambda item: len(item.label), reverse=True):
            names = (node.label, *node.aliases)
            for name in names:
                if len(name) >= 3 and name.lower() in query_lower:
                    key = (name.lower(), node.node_type)
                    entities[key] = ExtractedEntity(name, node.node_type, 0.98)
                    break

        return list(entities.values())

