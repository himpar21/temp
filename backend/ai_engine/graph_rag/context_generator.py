"""Generate structured, LLM-ready context from ranked graph paths."""

from __future__ import annotations

from ai_engine.graph_rag.entity_extractor import ProcessedGraphQuery
from ai_engine.graph_rag.entity_linker import LinkedEntity
from ai_engine.graph_rag.scoring import RankedPath


def generate_graph_context(
    query: ProcessedGraphQuery,
    linked_entities: list[LinkedEntity],
    paths: list[RankedPath],
    confidence: float,
) -> str:
    seeds = ", ".join(
        f"{item.node.label} ({item.node.node_type.value})" for item in linked_entities
    ) or "No exact entity link"
    sections = [
        f"[Graph RAG | intent={query.intent} | confidence={confidence:.3f}]",
        f"Linked entities: {seeds}",
    ]
    included_sources: set[str] = set()
    for rank, ranked in enumerate(paths, start=1):
        path = ranked.path
        chain_parts = [path.nodes[0].label]
        for edge, node in zip(path.edges, path.nodes[1:]):
            chain_parts.append(f"-[{edge.relationship.value}]-> {node.label}")
        terminal = path.nodes[-1]
        details = "; ".join(
            f"{key}={value}"
            for key, value in terminal.properties.items()
            if key in {"title", "project", "module", "priority", "status", "source"}
        )
        sections.append(
            f"Path {rank} (score={ranked.score:.3f}, strength="
            f"{ranked.relationship_strength:.3f}): {' '.join(chain_parts)}"
            + (f"\nEvidence: {details}" if details else "")
        )
        for node in path.nodes:
            content = str(node.properties.get("content", "")).strip()
            source_key = str(
                node.properties.get("source_document_id", node.node_id)
            )
            if content and source_key not in included_sources:
                included_sources.add(source_key)
                sections.append(
                    f"Source evidence for {node.label}:\n{content[:3000]}"
                )
    return "\n\n".join(sections)
