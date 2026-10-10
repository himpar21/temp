"""Threshold-based Hybrid RAG planning."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from ai_engine.graph_rag.graph_retriever import GraphRAGRetriever, GraphRetrievalResult
from ai_engine.hybrid_rag.router import (
    PlannerStatus,
    RetrievalSource,
    choose_retrieval_source,
)
from ai_engine.hybrid_rag.threshold import (
    DEFAULT_FALLBACK_THRESHOLD,
    DEFAULT_RELEVANCE_THRESHOLD,
    ThresholdEvaluation,
    evaluate_relevance,
)
from ai_engine.vanilla_rag.retriever import RetrievalResult, VanillaRAGRetriever
from database.vector.qdrant_client import SearchResult


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HybridRAGPlan:
    """Planner output forwarded to Graph RAG or response generation."""

    vanilla_result: RetrievalResult
    evaluation: ThresholdEvaluation
    selected_source: RetrievalSource
    status: PlannerStatus
    next_stage: str
    selected_context: str | None
    selected_chunks: list[SearchResult]
    decision_reason: str
    graph_result: GraphRetrievalResult | None = None


class HybridRAGPlanner:
    """Run Vanilla RAG first and select a downstream retrieval path."""

    def __init__(
        self,
        vanilla_retriever: VanillaRAGRetriever | None = None,
        graph_retriever: GraphRAGRetriever | None = None,
    ) -> None:
        self.vanilla_retriever = vanilla_retriever or VanillaRAGRetriever()
        self.graph_retriever = graph_retriever or GraphRAGRetriever()

    def plan(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
    ) -> HybridRAGPlan:
        vanilla_result = self.vanilla_retriever.retrieve(query, top_k)
        evaluation = evaluate_relevance(vanilla_result.relevance_score, threshold)
        selected_source = choose_retrieval_source(evaluation)

        if selected_source is RetrievalSource.VANILLA_RAG:
            return HybridRAGPlan(
                vanilla_result=vanilla_result,
                evaluation=evaluation,
                selected_source=selected_source,
                status=PlannerStatus.CONTEXT_SELECTED,
                next_stage="augmentation_response_generation",
                selected_context=vanilla_result.retrieved_context,
                selected_chunks=vanilla_result.chunks,
                decision_reason=(
                    "Vanilla RAG relevance meets the configured threshold; "
                    "its context is selected for downstream augmentation."
                ),
            )

        try:
            graph_result = self.graph_retriever.retrieve(query, top_k=top_k)
        except Exception as exc:
            logger.warning(
                "Graph RAG retrieval failed; evaluating Vanilla fallback: %s", exc
            )
            if (
                vanilla_result.chunks
                and vanilla_result.relevance_score >= DEFAULT_FALLBACK_THRESHOLD
            ):
                return HybridRAGPlan(
                    vanilla_result=vanilla_result,
                    evaluation=evaluation,
                    selected_source=RetrievalSource.VANILLA_RAG,
                    status=PlannerStatus.CONTEXT_SELECTED,
                    next_stage="augmentation_response_generation",
                    selected_context=vanilla_result.retrieved_context,
                    selected_chunks=vanilla_result.chunks,
                    decision_reason=(
                        "Graph RAG retrieval failed; usable Vanilla evidence was "
                        f"selected as a safe fallback ({type(exc).__name__})."
                    ),
                )
            raise
        if not graph_result.paths:
            if (
                vanilla_result.chunks
                and vanilla_result.relevance_score >= DEFAULT_FALLBACK_THRESHOLD
            ):
                return HybridRAGPlan(
                    vanilla_result=vanilla_result,
                    evaluation=evaluation,
                    selected_source=RetrievalSource.VANILLA_RAG,
                    status=PlannerStatus.CONTEXT_SELECTED,
                    next_stage="augmentation_response_generation",
                    selected_context=vanilla_result.retrieved_context,
                    selected_chunks=vanilla_result.chunks,
                    decision_reason=(
                        "Vanilla RAG relevance is below the configured threshold and "
                        "Graph RAG found no linked paths; usable vanilla evidence is "
                        "selected as a safe fallback."
                    ),
                    graph_result=graph_result,
                )
            return HybridRAGPlan(
                vanilla_result=vanilla_result,
                evaluation=evaluation,
                selected_source=selected_source,
                status=PlannerStatus.NO_CONTEXT_FOUND,
                next_stage="no_context",
                selected_context=None,
                selected_chunks=[],
                decision_reason=(
                    "Vanilla RAG relevance is below the configured threshold, "
                    "and Graph RAG found no linked traversal paths."
                ),
                graph_result=graph_result,
            )
        return HybridRAGPlan(
            vanilla_result=vanilla_result,
            evaluation=evaluation,
            selected_source=selected_source,
            status=PlannerStatus.GRAPH_CONTEXT_SELECTED,
            next_stage="augmentation_response_generation",
            selected_context=graph_result.graph_context,
            selected_chunks=[],
            decision_reason=(
                "Vanilla RAG relevance is below the configured threshold; "
                "Graph RAG relationship context is selected for downstream augmentation."
            ),
            graph_result=graph_result,
        )
