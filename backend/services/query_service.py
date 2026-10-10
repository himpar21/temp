"""PostgreSQL-backed retrieval over preprocessed uploaded document chunks."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ai_engine.llm.response_generator import ResponseGenerator, get_response_generator
from database.postgres.models import StoredChunk, StoredDocument


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
ENTITY_ID_PATTERN = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b", re.IGNORECASE)
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "i", "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "was", "what", "when", "where", "which", "who", "why", "with",
}


@dataclass(slots=True)
class RetrievedChunk:
    id: str
    source_id: str
    filename: str
    text: str
    score: float


def content_tokens(text: str) -> set[str]:
    return {
        token
        for token in TOKEN_PATTERN.findall(text.lower())
        if token not in STOP_WORDS and len(token) > 1
    }


def extract_query_entity_ids(question: str) -> list[str]:
    """Return stable artifact IDs such as DR-BUG-0026 and REQ-0345."""
    return list(dict.fromkeys(match.upper() for match in ENTITY_ID_PATTERN.findall(question)))


def lexical_score(question: str, text: str) -> float:
    query_tokens = content_tokens(question)
    if not query_tokens:
        return 0.0
    lowered = text.lower()
    text_tokens = content_tokens(text)
    coverage = len(query_tokens & text_tokens) / len(query_tokens)
    phrase = " ".join(TOKEN_PATTERN.findall(question.lower()))
    phrase_no_stop = " ".join(
        t for t in TOKEN_PATTERN.findall(question.lower()) if t not in STOP_WORDS
    )
    exact_bonus = 0.15 if phrase and phrase in lowered else 0.0
    if phrase_no_stop and phrase_no_stop in lowered:
        exact_bonus = max(exact_bonus, 0.15)
    return round(min(1.0, coverage * 0.85 + exact_bonus), 4)


class QueryService:
    def __init__(
        self,
        session: Session,
        response_generator: ResponseGenerator | None = None,
    ) -> None:
        self.session = session
        self._generator = response_generator or get_response_generator()

    def query(self, question: str, top_k: int = 5) -> dict:
        direct_documents = self._direct_documents(question)
        direct_document_ids = {document.id for document in direct_documents}
        candidates = (
            self._document_chunks(direct_document_ids)
            if direct_documents
            else self._candidates(question, max(top_k * 10, 50))
        )
        ranked = sorted(
            (
                RetrievedChunk(
                    id=chunk.id,
                    source_id=document.logical_document_id,
                    filename=document.filename,
                    text=chunk.text,
                    score=(
                        max(0.95, lexical_score(question, chunk.text))
                        if document.id in direct_document_ids
                        else lexical_score(question, chunk.text)
                    ),
                )
                for chunk, document in candidates
            ),
            key=lambda item: item.score,
            reverse=True,
        )
        relevant = [item for item in ranked if item.score > 0][:top_k]
        top_score = relevant[0].score if relevant else 0.0

        # An explicit artifact ID is authoritative: provide the complete source
        # document so sections that do not repeat the ID are not lost.
        if direct_documents:
            vanilla_context = "\n\n".join(
                f"[{document.filename} | exact entity match]\n{document.text}"
                for document in direct_documents
            )
        else:
            vanilla_context = (
                "\n\n".join(
                    f"[{item.filename} | score={item.score}]\n{item.text}"
                    for item in relevant
                )
                if relevant
                else None
            )

        # Generate a grounded answer with Qwen
        response = self._generator.generate(question, vanilla_context=vanilla_context)

        return {
            "answer": response.answer,
            "vanilla_score": top_score,
            "chunks": [
                {
                    "id": item.id,
                    "source_type": "UploadedDocument",
                    "source_id": item.source_id,
                    "filename": item.filename,
                    "text": item.text,
                    "score": item.score,
                }
                for item in relevant
            ],
        }

    def _direct_documents(self, question: str) -> list[StoredDocument]:
        entity_ids = extract_query_entity_ids(question)
        if not entity_ids:
            return []

        conditions = []
        for entity_id in entity_ids:
            conditions.extend((
                func.upper(StoredDocument.logical_document_id) == entity_id,
                StoredDocument.entity_ids.contains([entity_id]),
            ))
        statement = (
            select(StoredDocument)
            .where(or_(*conditions))
            .order_by(StoredDocument.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def _document_chunks(self, document_ids: set[str]):
        statement = (
            select(StoredChunk, StoredDocument)
            .join(StoredDocument, StoredDocument.id == StoredChunk.document_id)
            .where(StoredDocument.id.in_(document_ids))
            .order_by(StoredDocument.created_at.desc(), StoredChunk.chunk_index)
        )
        return self.session.execute(statement).all()

    def _candidates(self, question: str, limit: int):
        vector  = func.to_tsvector("english", StoredChunk.text)
        tsquery = func.websearch_to_tsquery("english", question)
        statement = (
            select(StoredChunk, StoredDocument)
            .join(StoredDocument, StoredDocument.id == StoredChunk.document_id)
            .where(vector.op("@@")(tsquery))
            .order_by(func.ts_rank_cd(vector, tsquery).desc())
            .limit(limit)
        )
        candidates = self.session.execute(statement).all()
        if candidates:
            return candidates

        # Fallback: ILIKE token matching when full-text search returns nothing
        tokens = sorted(content_tokens(question), key=len, reverse=True)[:8]
        if not tokens:
            return []
        fallback = (
            select(StoredChunk, StoredDocument)
            .join(StoredDocument, StoredDocument.id == StoredChunk.document_id)
            .where(or_(*(StoredChunk.text.ilike(f"%{token}%") for token in tokens)))
            .limit(limit)
        )
        return self.session.execute(fallback).all()
