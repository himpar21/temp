"""Parsers that turn source files into normalized document records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ingestion.models import SourceDocument
from ingestion.preprocessing import (
    clean_text,
    extract_entity_ids,
    infer_document_type,
    infer_primary_entity_id,
    parse_front_matter,
    sha256_bytes,
)


def parse_markdown(path: Path, dataset_root: Path) -> SourceDocument:
    raw = path.read_bytes()
    text = clean_text(raw.decode("utf-8-sig"))
    metadata, body = parse_front_matter(text)
    relative_path = path.relative_to(dataset_root).as_posix()
    document_id = str(
        metadata.get("document_id")
        or metadata.get("requirement_id")
        or metadata.get("test_case_id")
        or metadata.get("failure_id")
        or metadata.get("defect_id")
        or path.stem
    )
    document_type = infer_document_type(path, metadata)
    metadata.update(
        {
            "source_path": relative_path,
            "source_type": "markdown",
            "filename": path.name,
        }
    )
    return SourceDocument(
        document_id=document_id,
        source_path=relative_path,
        source_type="markdown",
        document_type=document_type,
        text=body,
        metadata=metadata,
        entity_ids=extract_entity_ids(body, metadata),
        content_hash=sha256_bytes(raw),
    )


def parse_pdf(path: Path, dataset_root: Path) -> SourceDocument:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depends on optional runtime package
        raise RuntimeError("PDF ingestion requires the 'pypdf' package") from exc

    raw = path.read_bytes()
    reader = PdfReader(path)
    page_text = [page.extract_text() or "" for page in reader.pages]
    body = clean_text("\n\n".join(page_text))
    if not body:
        raise ValueError("PDF contains no extractable text; OCR is required")

    relative_path = path.relative_to(dataset_root).as_posix()
    metadata: dict[str, Any] = {
        "source_path": relative_path,
        "source_type": "pdf",
        "filename": path.name,
        "page_count": len(reader.pages),
        "ocr_required": False,
    }
    if reader.metadata:
        for key, value in reader.metadata.items():
            if value is not None:
                metadata[f"pdf_{str(key).lstrip('/').lower()}"] = clean_text(str(value))
    document_type = infer_document_type(path, metadata)
    entity_ids = extract_entity_ids(body, metadata)
    document_id = infer_primary_entity_id(path, entity_ids)
    if document_id not in entity_ids:
        entity_ids = sorted({*entity_ids, document_id})
    return SourceDocument(
        document_id=document_id,
        source_path=relative_path,
        source_type="pdf",
        document_type=document_type,
        text=body,
        metadata=metadata,
        entity_ids=entity_ids,
        content_hash=sha256_bytes(raw),
    )


def parse_document(path: Path, dataset_root: Path) -> SourceDocument:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return parse_markdown(path, dataset_root)
    if suffix == ".pdf":
        return parse_pdf(path, dataset_root)
    raise ValueError(f"Unsupported document type: {suffix}")

