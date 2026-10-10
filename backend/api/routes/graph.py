"""Graph RAG retrieval API."""

from functools import lru_cache

from fastapi import APIRouter, Depends

from ai_engine.graph_rag.graph_retriever import GraphRAGRetriever, GraphRetrievalResult
from ai_engine.llm.response_generator import ResponseGenerator, get_response_generator
from schemas.request.query_schema import GraphRAGQuery
from schemas.response.rag_response import (
    GraphEntityResponse,
    GraphPathResponse,
    GraphRAGResponse,
    GraphRetrievalMetrics,
)
from services.graph_projection_service import load_uploaded_graph


router = APIRouter(prefix="/api/v1/graph-rag", tags=["Graph RAG"])


@lru_cache(maxsize=1)
def get_graph_retriever() -> GraphRAGRetriever:
    return GraphRAGRetriever(dynamic_loader=load_uploaded_graph)


def serialize_graph_result(result: GraphRetrievalResult) -> GraphRAGResponse:
    return GraphRAGResponse(
        query=result.query,
        processed_query=result.processed_query.normalized,
        intent=result.processed_query.intent,
        keywords=list(result.processed_query.keywords),
        extracted_entities=[entity.mention for entity in result.extracted_entities],
        linked_entities=[
            GraphEntityResponse(
                node_id=entity.node.node_id,
                node_type=entity.node.node_type.value,
                label=entity.node.label,
                confidence=round(entity.confidence, 6),
            )
            for entity in result.linked_entities
        ],
        generated_graph_query=result.generated_query,
        paths=[
            GraphPathResponse(
                rank=rank,
                node_ids=[node.node_id for node in item.path.nodes],
                labels=[node.label for node in item.path.nodes],
                node_types=[node.node_type.value for node in item.path.nodes],
                relationships=[edge.relationship.value for edge in item.path.edges],
                hops=item.path.hops,
                score=round(item.score, 6),
                relationship_strength=round(item.relationship_strength, 6),
            )
            for rank, item in enumerate(result.paths, start=1)
        ],
        graph_context=result.graph_context,
        confidence_score=round(result.confidence_score, 6),
        metrics=GraphRetrievalMetrics(
            nodes_scanned=result.nodes_scanned,
            paths_considered=result.paths_considered,
            retrieval_latency_ms=round(result.latency_ms, 3),
        ),
    )


@router.post("/query", response_model=GraphRAGResponse)
def query_graph_rag(
    request: GraphRAGQuery,
    retriever: GraphRAGRetriever = Depends(get_graph_retriever),
    generator: ResponseGenerator = Depends(get_response_generator),
) -> GraphRAGResponse:
    result = retriever.retrieve(request.query, request.top_k, request.max_hops)
    response = serialize_graph_result(result)
    generated = generator.generate(
        request.query,
        graph_context=result.graph_context if result.paths else None,
    )
    return response.model_copy(update={"answer": generated.answer})

