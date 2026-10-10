"""Upload endpoints that automatically run preprocessing and persistence."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import Text, cast, func, or_, select
from sqlalchemy.orm import Session

from database.postgres.connection import get_db
from database.postgres.models import IngestionJob, StoredDocument, StructuredRecord
from schemas.request.upload_schema import (
    IngestionJobResponse,
    StructuredRecordsResponse,
    StructuredTableResponse,
    UploadedDocumentResponse,
    UploadIngestionResponse,
)
from services.upload_ingestion_service import MAX_UPLOAD_BYTES, UploadIngestionService


router = APIRouter(prefix="/ingestion", tags=["ingestion"])


def _job_response(job: IngestionJob) -> IngestionJobResponse:
    return IngestionJobResponse(
        job_id=job.id,
        status=job.status,
        filename=job.filename,
        error_message=job.error_message,
        documents=job.document_count,
        structured_records=job.structured_record_count,
        chunks=job.chunk_count,
    )


def _structured_columns(record: StructuredRecord, document: StoredDocument | None) -> list[str]:
    metadata_columns = (document.document_metadata or {}).get("columns") if document else None
    if isinstance(metadata_columns, list) and all(isinstance(column, str) for column in metadata_columns):
        return metadata_columns
    return list((record.payload or {}).keys())


@router.get("/documents", response_model=list[UploadedDocumentResponse])
def uploaded_documents(
    search: str | None = Query(default=None, max_length=200),
    source_type: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[UploadedDocumentResponse]:
    """List ingested documents for the frontend Data Browser."""
    statement = select(StoredDocument)
    if source_type and source_type.strip():
        statement = statement.where(StoredDocument.source_type == source_type.strip().lower())
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                StoredDocument.filename.ilike(pattern),
                StoredDocument.logical_document_id.ilike(pattern),
                StoredDocument.document_type.ilike(pattern),
            )
        )
    documents = db.scalars(
        statement.order_by(StoredDocument.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return [
        UploadedDocumentResponse(
            id=document.id,
            logical_document_id=document.logical_document_id,
            filename=document.filename,
            content_type=document.content_type,
            source_type=document.source_type,
            document_type=document.document_type,
            source_path=str((document.document_metadata or {}).get("source_path") or document.filename),
            entity_ids=document.entity_ids or [],
            created_at=document.created_at,
        )
        for document in documents
    ]


@router.get("/structured-tables", response_model=list[StructuredTableResponse])
def structured_tables(db: Session = Depends(get_db)) -> list[StructuredTableResponse]:
    """List every ingested CSV/structured dataset as a separate browser table."""
    counts = db.execute(
        select(StructuredRecord.record_type, func.count(StructuredRecord.id))
        .group_by(StructuredRecord.record_type)
        .order_by(StructuredRecord.record_type)
    ).all()
    tables: list[StructuredTableResponse] = []
    for record_type, row_count in counts:
        sample = db.execute(
            select(StructuredRecord, StoredDocument)
            .join(StoredDocument, StoredDocument.id == StructuredRecord.document_id)
            .where(StructuredRecord.record_type == record_type)
            .order_by(StructuredRecord.id)
            .limit(1)
        ).first()
        if not sample:
            continue
        record, document = sample
        tables.append(
            StructuredTableResponse(
                record_type=record_type,
                label=record_type.replace("_", " ").title(),
                columns=_structured_columns(record, document),
                row_count=row_count,
            )
        )
    return tables


@router.get("/structured-records/{record_type}", response_model=StructuredRecordsResponse)
def structured_records(
    record_type: str,
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=500, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> StructuredRecordsResponse:
    """Return rows using the original headers for one structured CSV dataset."""
    filters = [StructuredRecord.record_type == record_type]
    if search and search.strip():
        filters.append(cast(StructuredRecord.payload, Text).ilike(f"%{search.strip()}%"))

    total = db.scalar(select(func.count(StructuredRecord.id)).where(*filters)) or 0
    rows = db.scalars(
        select(StructuredRecord)
        .where(*filters)
        .order_by(StructuredRecord.id)
        .offset(offset)
        .limit(limit)
    ).all()
    if not rows:
        table_exists = db.scalar(
            select(StructuredRecord.id).where(StructuredRecord.record_type == record_type).limit(1)
        )
        if table_exists is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Structured dataset not found")

    sample = db.execute(
        select(StructuredRecord, StoredDocument)
        .join(StoredDocument, StoredDocument.id == StructuredRecord.document_id)
        .where(StructuredRecord.record_type == record_type)
        .order_by(StructuredRecord.id)
        .limit(1)
    ).first()
    columns = _structured_columns(*sample) if sample else []
    return StructuredRecordsResponse(
        record_type=record_type,
        columns=columns,
        total=total,
        rows=[record.payload for record in rows],
    )


@router.post("/upload", response_model=UploadIngestionResponse, status_code=status.HTTP_201_CREATED)
async def upload_and_ingest(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadIngestionResponse:
    """Upload, preprocess, chunk, and persist a document automatically."""
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    try:
        result = UploadIngestionService(db).ingest(file.filename or "upload", file.content_type, content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return UploadIngestionResponse(**result)


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
def ingestion_job(job_id: str, db: Session = Depends(get_db)) -> IngestionJobResponse:
    job = db.get(IngestionJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found")
    return _job_response(job)


@router.post("/jobs/{job_id}/retry-indexing", response_model=IngestionJobResponse)
def retry_ingestion_index(job_id: str, db: Session = Depends(get_db)) -> IngestionJobResponse:
    """Retry an idempotent Qdrant backfill using chunks already in PostgreSQL."""
    job = db.get(IngestionJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found")
    try:
        updated_job = UploadIngestionService(db).retry_indexing(job)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return _job_response(updated_job)

