"""Upload response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class UploadIngestionResponse(BaseModel):
    job_id: str
    status: str
    filename: str
    duplicate: bool = False
    document_id: str | None = None
    structured_records: int = 0
    chunks: int = 0
    graph_nodes: int = 0
    graph_edges: int = 0
    error_message: str | None = None


class IngestionJobResponse(BaseModel):
    job_id: str
    status: str
    filename: str
    error_message: str | None = None
    documents: int
    structured_records: int
    chunks: int


class UploadedDocumentResponse(BaseModel):
    id: str
    logical_document_id: str
    filename: str
    content_type: str | None
    source_type: str
    document_type: str
    source_path: str
    entity_ids: list[str]
    created_at: datetime


class StructuredTableResponse(BaseModel):
    record_type: str
    label: str
    columns: list[str]
    row_count: int


class StructuredRecordsResponse(BaseModel):
    record_type: str
    columns: list[str]
    total: int
    rows: list[dict[str, Any]]

