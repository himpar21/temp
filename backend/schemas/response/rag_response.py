"""RAG response schemas."""

from typing import Any

from pydantic import BaseModel, Field

from ai_engine.hybrid_rag.router import PlannerStatus, RetrievalSource


class RetrievedChunkResponse(BaseModel):
    id: str
    source_type: str
    source_id: str
    filename: str
    text: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    vanilla_score: float
    chunks: list[RetrievedChunkResponse]

class RetrievedChunk(BaseModel):
    rank: int
    chunk_id: str
    artifact_id: str
    artifact_type: str
    title: str
    content: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    relevance_score: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any]


class RetrievalMetrics(BaseModel):
    embedding_model: str
    embedding_dimension: int
    candidates_scanned: int
    retrieval_latency_ms: float


class VanillaRAGResponse(BaseModel):
    query: str
    processed_query: str
    top_k: int
    query_embedding: list[float]
    relevance_score: float = Field(ge=0.0, le=1.0)
    retrieved_context: str
    answer: str = ""          # LLM-generated answer (empty if LLM unavailable)
    chunks: list[RetrievedChunk]
    metrics: RetrievalMetrics


class GraphEntityResponse(BaseModel):
    node_id: str
    node_type: str
    label: str
    confidence: float = Field(ge=0.0, le=1.0)


class GraphPathResponse(BaseModel):
    rank: int
    node_ids: list[str]
    labels: list[str]
    node_types: list[str]
    relationships: list[str]
    hops: int
    score: float = Field(ge=0.0, le=1.0)
    relationship_strength: float = Field(ge=0.0, le=1.0)


class GraphRetrievalMetrics(BaseModel):
    nodes_scanned: int
    paths_considered: int
    retrieval_latency_ms: float


class GraphRAGResponse(BaseModel):
    query: str
    processed_query: str
    intent: str
    keywords: list[str]
    extracted_entities: list[str]
    linked_entities: list[GraphEntityResponse]
    generated_graph_query: str
    paths: list[GraphPathResponse]
    graph_context: str
    answer: str = ""
    confidence_score: float = Field(ge=0.0, le=1.0)
    metrics: GraphRetrievalMetrics


class ThresholdDecision(BaseModel):
    vanilla_relevance_score: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    comparison: str
    threshold_met: bool
    selected_source: RetrievalSource
    status: PlannerStatus
    reason: str


class PipelineStageResponse(BaseModel):
    stage: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class HybridRAGPlanResponse(BaseModel):
    query: str
    processed_query: str
    top_k: int
    decision: ThresholdDecision
    answer: str = ""
    selected_context: str | None
    selected_chunks: list[RetrievedChunk]
    vanilla_candidates: list[RetrievedChunk]
    next_stage: str
    graph_rag_available: bool = True
    graph_result: GraphRAGResponse | None = None
    metrics: RetrievalMetrics
    pipeline_trace: list[PipelineStageResponse] = Field(default_factory=list)
