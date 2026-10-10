"""Query routes — Qdrant semantic search and PostgreSQL full-text search."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ai_engine.llm.response_generator import ResponseGenerator, get_response_generator
from ai_engine.vanilla_rag.retriever import VanillaRAGRetriever
from database.postgres.connection import get_db
from database.vector.qdrant_client import get_qdrant_client
from schemas.request.query_schema import QueryRequest, VanillaRAGQuery
from schemas.response.rag_response import (
    QueryResponse,
    RetrievalMetrics,
    RetrievedChunk,
    VanillaRAGResponse,
)
from services.query_service import QueryService


router = APIRouter(tags=["query"])


def get_retriever() -> VanillaRAGRetriever:
    """Build the Qdrant-backed retriever (singleton via Qdrant client)."""
    return VanillaRAGRetriever(qdrant=get_qdrant_client())


# ── PostgreSQL-backed query (uploaded documents, full-text search) ─────────

@router.post("/query", response_model=QueryResponse)
def query_documents(
    request: QueryRequest,
    db: Session = Depends(get_db),
    generator: ResponseGenerator = Depends(get_response_generator),
) -> QueryResponse:
    return QueryResponse(**QueryService(db, generator).query(request.question, request.top_k))


# ── Qdrant-backed semantic RAG query ───────────────────────────────────────

@router.post("/rag/query", response_model=VanillaRAGResponse, tags=["Vanilla RAG"])
def query_vanilla_rag(
    request: VanillaRAGQuery,
    generator: ResponseGenerator = Depends(get_response_generator),
) -> VanillaRAGResponse:
    retriever = get_retriever()
    result    = retriever.retrieve(request.query, request.top_k)

    chunks = [
        RetrievedChunk(
            rank=rank,
            chunk_id=chunk.id,
            artifact_id=chunk.document_id,
            artifact_type=chunk.metadata.get("document_type", "chunk"),
            title=chunk.filename,
            content=chunk.text,
            similarity_score=round(chunk.score, 6),
            relevance_score=round(chunk.score, 6),
            metadata=chunk.metadata,
        )
        for rank, chunk in enumerate(result.chunks, start=1)
    ]

    llm_response = generator.generate(
        request.query,
        vanilla_context=result.retrieved_context,
    )

    return VanillaRAGResponse(
        query=result.query,
        processed_query=result.processed_query,
        top_k=len(chunks),
        query_embedding=result.query_embedding,
        relevance_score=round(result.relevance_score, 6),
        retrieved_context=result.retrieved_context,
        answer=llm_response.answer,
        chunks=chunks,
        metrics=RetrievalMetrics(
            embedding_model=retriever.embedding_model.name,
            embedding_dimension=retriever.embedding_model.dimension,
            candidates_scanned=result.candidates_scanned,
            retrieval_latency_ms=round(result.latency_ms, 3),
        ),
    )
