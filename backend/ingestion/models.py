"""Data contracts shared by the ingestion and preprocessing pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class SourceDocument:
    document_id: str
    source_path: str
    source_type: str
    document_type: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    entity_ids: list[str] = field(default_factory=list)
    content_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    source_path: str
    document_type: str
    section: str
    chunk_index: int
    text: str
    metadata: dict[str, Any]
    entity_ids: list[str]
    content_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class IngestionIssue:
    source_path: str
    stage: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
