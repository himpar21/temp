"""End-to-end Graph RAG retrieval pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable

from ai_engine.graph_rag.context_generator import generate_graph_context
from ai_engine.graph_rag.entity_extractor import (
    EntityExtractor,
    ExtractedEntity,
    ProcessedGraphQuery,
)
from ai_engine.graph_rag.entity_linker import EntityLinker, LinkedEntity
from ai_engine.graph_rag.graph_builder import DEFAULT_DATASET_PATH, GraphBuilder
from ai_engine.graph_rag.query_generator import generate_graph_query
from ai_engine.graph_rag.scoring import RankedPath, graph_confidence, rank_paths
from ai_engine.graph_rag.traversal import GraphTraverser
from database.graph.graph_schema import KnowledgeGraph


@dataclass(frozen=True)
class GraphRetrievalResult:
    query: str
    processed_query: ProcessedGraphQuery
    extracted_entities: list[ExtractedEntity]
    linked_entities: list[LinkedEntity]
    generated_query: str
    paths: list[RankedPath]
    graph_context: str
    confidence_score: float
    nodes_scanned: int
    paths_considered: int
    latency_ms: float


class GraphRAGRetriever:
    """Execute preprocessing, NER, linking, traversal, ranking and context."""

    def __init__(
        self,
        dataset_path: Path | str = DEFAULT_DATASET_PATH,
        dynamic_loader: Callable[[], KnowledgeGraph | None] | None = None,
    ) -> None:
        self.graph = GraphBuilder(dataset_path).build()
        self.dynamic_loader = dynamic_loader
        self.extractor = EntityExtractor()
        self.linker = EntityLinker()
        self.traverser = GraphTraverser()

    def retrieve(
        self, query: str, top_k: int = 5, max_hops: int = 4
    ) -> GraphRetrievalResult:
        if not 1 <= top_k <= 20:
            raise ValueError("top_k must be between 1 and 20")
        started_at = perf_counter()
        graph = self.graph
        if self.dynamic_loader is not None:
            dynamic_graph = self.dynamic_loader()
            if dynamic_graph is not None:
                graph = graph.merged_with(dynamic_graph)
        processed = self.extractor.preprocess(query)
        entities = self.extractor.extract(processed, graph)
        linked = self.linker.link(entities, processed, graph)
        generated_query = generate_graph_query(processed, linked, max_hops)
        traversed = self.traverser.traverse(graph, linked, max_hops)
        ranked = rank_paths(traversed, processed, graph, top_k)
        confidence = graph_confidence(ranked, len(linked))
        context = generate_graph_context(processed, linked, ranked, confidence)
        latency_ms = (perf_counter() - started_at) * 1000
        return GraphRetrievalResult(
            query=query,
            processed_query=processed,
            extracted_entities=entities,
            linked_entities=linked,
            generated_query=generated_query,
            paths=ranked,
            graph_context=context,
            confidence_score=confidence,
            nodes_scanned=len(graph.nodes),
            paths_considered=len(traversed),
            latency_ms=latency_ms,
        )

