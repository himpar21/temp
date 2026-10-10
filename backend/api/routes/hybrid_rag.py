"""API route for threshold-based Hybrid RAG planning."""

from functools import lru_cache

from fastapi import APIRouter, Depends

from api.routes.graph import serialize_graph_result
from ai_engine.graph_rag.graph_retriever import GraphRAGRetriever
from ai_engine.hybrid_rag.planner import HybridRAGPlanner
from ai_engine.hybrid_rag.router import RetrievalSource
from ai_engine.llm.response_generator import ResponseGenerator, get_response_generator
from database.vector.qdrant_client import SearchResult
from schemas.request.query_schema import HybridRAGPlanQuery
from schemas.response.rag_response import (
    HybridRAGPlanResponse,
    PipelineStageResponse,
    RetrievalMetrics,
    RetrievedChunk,
    ThresholdDecision,
)
from services.graph_projection_service import load_uploaded_graph


router = APIRouter(prefix="/api/v1/hybrid-rag", tags=["Hybrid RAG Planner"])


@lru_cache(maxsize=1)
def get_planner() -> HybridRAGPlanner:
    """Build the planner and its Vanilla RAG index once per API process."""

    return HybridRAGPlanner(
        graph_retriever=GraphRAGRetriever(dynamic_loader=load_uploaded_graph)
    )


def _serialize_chunks(results: list[SearchResult]) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            rank=rank,
            chunk_id=item.id,
            artifact_id=item.document_id,
            artifact_type=item.metadata.get("document_type", "chunk"),
            title=item.filename,
            content=item.text,
            similarity_score=round(item.score, 6),
            relevance_score=round(item.score, 6),
            metadata=item.metadata,
        )
        for rank, item in enumerate(results, start=1)
    ]


def _execute_pipeline(
    request: HybridRAGPlanQuery,
    planner: HybridRAGPlanner,
    generator: ResponseGenerator | None = None,
) -> HybridRAGPlanResponse:
    plan = planner.plan(request.query, request.top_k)
    vanilla_result = plan.vanilla_result
    candidates = _serialize_chunks(vanilla_result.chunks)
    selected_chunks = (
        candidates if plan.selected_source is RetrievalSource.VANILLA_RAG else []
    )

    graph_response = (
        serialize_graph_result(plan.graph_result) if plan.graph_result else None
    )
    answer = ""
    if generator is not None:
        generated = generator.generate(
            request.query,
            vanilla_context=(
                plan.selected_context
                if plan.selected_source is RetrievalSource.VANILLA_RAG
                else None
            ),
            graph_context=(
                plan.selected_context
                if plan.selected_source is RetrievalSource.GRAPH_RAG
                else None
            ),
        )
        answer = generated.answer
    pipeline_trace = [
        PipelineStageResponse(
            stage="query_preprocessing",
            status="completed",
            details={"processed_query": vanilla_result.processed_query},
        ),
        PipelineStageResponse(
            stage="vanilla_rag_retrieval",
            status="completed",
            details={
                "relevance_score": round(plan.evaluation.score, 6),
                "candidates_retrieved": len(candidates),
            },
        ),
        PipelineStageResponse(
            stage="threshold_routing",
            status="completed",
            details={
                "threshold": plan.evaluation.threshold,
                "threshold_met": plan.evaluation.threshold_met,
                "selected_source": plan.selected_source.value,
            },
        ),
        PipelineStageResponse(
            stage="graph_rag_retrieval",
            status=(
                "completed"
                if graph_response and graph_response.paths
                else "no_results"
                if graph_response
                else "skipped"
            ),
            details=(
                {
                    "confidence_score": graph_response.confidence_score,
                    "paths_returned": len(graph_response.paths),
                }
                if graph_response
                else {
                    "reason": (
                        "Vanilla RAG score met the threshold"
                        if plan.evaluation.threshold_met
                        else plan.decision_reason
                    )
                }
            ),
        ),
        PipelineStageResponse(
            stage="context_selection",
            status="completed" if plan.selected_context else "no_context",
            details={
                "selected_source": plan.selected_source.value,
                "next_stage": plan.next_stage,
            },
        ),
    ]
    if generator is not None:
        pipeline_trace.append(
            PipelineStageResponse(
                stage="llm_generation",
                status="completed",
                details={"context_source": plan.selected_source.value},
            )
        )

    return HybridRAGPlanResponse(
        query=vanilla_result.query,
        processed_query=vanilla_result.processed_query,
        top_k=len(candidates),
        answer=answer,
        decision=ThresholdDecision(
            vanilla_relevance_score=round(plan.evaluation.score, 6),
            threshold=plan.evaluation.threshold,
            comparison="Sv >= T",
            threshold_met=plan.evaluation.threshold_met,
            selected_source=plan.selected_source,
            status=plan.status,
            reason=plan.decision_reason,
        ),
        selected_context=plan.selected_context,
        selected_chunks=selected_chunks,
        vanilla_candidates=candidates,
        next_stage=plan.next_stage,
        graph_rag_available=True,
        graph_result=graph_response,
        metrics=RetrievalMetrics(
            embedding_model=planner.vanilla_retriever.embedding_model.name,
            embedding_dimension=planner.vanilla_retriever.embedding_model.dimension,
            candidates_scanned=vanilla_result.candidates_scanned,
            retrieval_latency_ms=round(vanilla_result.latency_ms, 3),
        ),
        pipeline_trace=pipeline_trace,
    )


@router.post(
    "/query",
    response_model=HybridRAGPlanResponse,
    summary="Execute the complete adaptive RAG retrieval flow",
)
def query_hybrid_rag(
    request: HybridRAGPlanQuery,
    planner: HybridRAGPlanner = Depends(get_planner),
    generator: ResponseGenerator = Depends(get_response_generator),
) -> HybridRAGPlanResponse:
    """Score Vanilla RAG, route by threshold, and execute Graph RAG if needed."""

    return _execute_pipeline(request, planner, generator)


@router.post(
    "/plan",
    response_model=HybridRAGPlanResponse,
    deprecated=True,
    summary="Compatibility alias for the complete adaptive RAG flow",
)
def plan_hybrid_rag(
    request: HybridRAGPlanQuery,
    planner: HybridRAGPlanner = Depends(get_planner),
    generator: ResponseGenerator = Depends(get_response_generator),
) -> HybridRAGPlanResponse:
    return _execute_pipeline(request, planner, generator)
