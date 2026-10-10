"""Retrieval routing decisions for the Hybrid RAG planner."""

from enum import Enum

from ai_engine.hybrid_rag.threshold import ThresholdEvaluation


class RetrievalSource(str, Enum):
    VANILLA_RAG = "vanilla_rag"
    GRAPH_RAG = "graph_rag"


class PlannerStatus(str, Enum):
    CONTEXT_SELECTED = "context_selected"
    GRAPH_RAG_REQUIRED = "graph_rag_required"
    GRAPH_CONTEXT_SELECTED = "graph_context_selected"
    NO_CONTEXT_FOUND = "no_context_found"


def choose_retrieval_source(evaluation: ThresholdEvaluation) -> RetrievalSource:
    """Route to Graph RAG only when Vanilla relevance is below threshold."""

    if evaluation.threshold_met:
        return RetrievalSource.VANILLA_RAG
    return RetrievalSource.GRAPH_RAG
