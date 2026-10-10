"""Batch and incremental ingestion for the synthetic test-management corpus."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from ingestion.chunking.chunk_generator import generate_chunks
from ingestion.models import IngestionIssue
from ingestion.parsers.document_parser import parse_document
from ingestion.preprocessing import normalize_scalar, sha256_bytes


ALLOWED_SOURCE_DIRECTORIES = ("structured", "unstructured", "pdf_documents")
EXCLUDED_DIRECTORIES = (
    "graph",
    "evaluation",
    "input_fixtures",
    "metadata",
    "pdf_metadata",
    "pdf_generation",
    "scripts",
)
PIPELINE_VERSION = 2


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    content = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    _atomic_write_text(path, content)


class IngestionService:
    """Ingest only primary structured and unstructured source folders.

    Benchmark fixtures, supplied graph files, generation utilities, and evaluation
    answers are intentionally unreachable through source discovery.
    """

    def __init__(
        self,
        dataset_root: Path,
        output_root: Path,
        *,
        include_pdfs: bool = True,
        max_chunk_words: int = 350,
        chunk_overlap_words: int = 50,
        fail_on_error: bool = False,
    ) -> None:
        self.dataset_root = dataset_root.resolve()
        self.output_root = output_root.resolve()
        self.include_pdfs = include_pdfs
        self.max_chunk_words = max_chunk_words
        self.chunk_overlap_words = chunk_overlap_words
        self.fail_on_error = fail_on_error
        self.issues: list[IngestionIssue] = []

    def _validate_roots(self) -> None:
        if not self.dataset_root.is_dir():
            raise FileNotFoundError(f"Dataset root does not exist: {self.dataset_root}")
        if not (self.dataset_root / "structured").is_dir():
            raise ValueError("Dataset root must contain a structured directory")
        if self.output_root == self.dataset_root or self.dataset_root in self.output_root.parents:
            raise ValueError("Output directory must be outside the source dataset")

    def _source_files(self) -> tuple[list[Path], list[Path]]:
        csv_files = sorted((self.dataset_root / "structured").glob("*.csv"))
        documents = sorted((self.dataset_root / "unstructured").rglob("*.md"))
        if self.include_pdfs:
            documents.extend(sorted((self.dataset_root / "pdf_documents").rglob("*.pdf")))
        return csv_files, documents

    def _record_issue(self, path: Path, stage: str, exc: Exception) -> None:
        relative = path.relative_to(self.dataset_root).as_posix()
        issue = IngestionIssue(relative, stage, f"{type(exc).__name__}: {exc}")
        self.issues.append(issue)
        if self.fail_on_error:
            raise exc

    def _normalize_csv(self, source: Path, target: Path) -> tuple[int, int, list[str]]:
        raw = source.read_bytes()
        decoded = raw.decode("utf-8-sig")
        reader = csv.DictReader(decoded.splitlines())
        if not reader.fieldnames:
            raise ValueError("CSV has no header")
        fields = [normalize_scalar(name) for name in reader.fieldnames]
        primary_key = fields[0]
        rows: list[dict[str, str]] = []
        seen: set[str] = set()
        duplicate_count = 0
        for line_number, source_row in enumerate(reader, start=2):
            row = {
                fields[index]: normalize_scalar(source_row.get(original) or "")
                for index, original in enumerate(reader.fieldnames)
            }
            key = row[primary_key]
            if not key:
                raise ValueError(f"Missing {primary_key} at line {line_number}")
            if key in seen:
                duplicate_count += 1
                continue
            seen.add(key)
            rows.append(row)

        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temp_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return len(rows), duplicate_count, fields

    def run(self) -> dict[str, Any]:
        self._validate_roots()
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.issues = []

        manifest_path = self.output_root / "manifest.json"
        old_manifest = _read_json(manifest_path, {"files": {}})
        cache_compatible = old_manifest.get("pipeline_version") == PIPELINE_VERSION
        old_files: dict[str, dict[str, Any]] = old_manifest.get("files", {})
        previous_documents = {
            record["source_path"]: record
            for record in _read_jsonl(self.output_root / "documents.jsonl")
        }
        previous_chunks: dict[str, list[dict[str, Any]]] = {}
        for record in _read_jsonl(self.output_root / "chunks.jsonl"):
            previous_chunks.setdefault(record["source_path"], []).append(record)

        csv_files, document_files = self._source_files()
        manifest_files: dict[str, dict[str, Any]] = {}
        structured_summary: dict[str, Any] = {}
        status_counts: Counter[str] = Counter()

        for source in csv_files:
            relative = source.relative_to(self.dataset_root).as_posix()
            digest = sha256_bytes(source.read_bytes())
            target = self.output_root / "structured" / source.name
            unchanged = (
                cache_compatible
                and old_files.get(relative, {}).get("sha256") == digest
                and target.exists()
            )
            try:
                if unchanged:
                    with target.open("r", encoding="utf-8-sig", newline="") as handle:
                        reader = csv.reader(handle)
                        header = next(reader)
                        row_count = sum(1 for _ in reader)
                    duplicate_count = 0
                else:
                    row_count, duplicate_count, header = self._normalize_csv(source, target)
                status = "unchanged" if unchanged else "processed"
                status_counts[status] += 1
                structured_summary[source.stem] = {
                    "rows": row_count,
                    "duplicates_removed": duplicate_count,
                    "columns": header,
                    "output": target.relative_to(self.output_root).as_posix(),
                }
                manifest_files[relative] = {
                    "sha256": digest,
                    "kind": "structured",
                    "status": status,
                    "records": row_count,
                }
            except Exception as exc:  # keep the batch observable and optionally resilient
                self._record_issue(source, "structured_preprocessing", exc)
                status_counts["failed"] += 1
                manifest_files[relative] = {"sha256": digest, "kind": "structured", "status": "failed"}

        documents: list[dict[str, Any]] = []
        chunks: list[dict[str, Any]] = []
        seen_hashes: dict[str, str] = {}
        for source in document_files:
            relative = source.relative_to(self.dataset_root).as_posix()
            digest = sha256_bytes(source.read_bytes())
            old_entry = old_files.get(relative, {})
            reusable = (
                cache_compatible
                and
                old_entry.get("sha256") == digest
                and relative in previous_documents
                and relative in previous_chunks
            )
            if digest in seen_hashes:
                status_counts["duplicate"] += 1
                manifest_files[relative] = {
                    "sha256": digest,
                    "kind": "document",
                    "status": "duplicate",
                    "duplicate_of": seen_hashes[digest],
                }
                continue
            seen_hashes[digest] = relative
            try:
                if reusable:
                    document_record = previous_documents[relative]
                    chunk_records = previous_chunks[relative]
                    status = "unchanged"
                else:
                    document = parse_document(source, self.dataset_root)
                    generated = generate_chunks(
                        document,
                        max_words=self.max_chunk_words,
                        overlap_words=self.chunk_overlap_words,
                    )
                    document_record = document.to_dict()
                    chunk_records = [chunk.to_dict() for chunk in generated]
                    status = "processed"
                documents.append(document_record)
                chunks.extend(chunk_records)
                status_counts[status] += 1
                manifest_files[relative] = {
                    "sha256": digest,
                    "kind": "document",
                    "status": status,
                    "document_id": document_record["document_id"],
                    "chunks": len(chunk_records),
                }
            except Exception as exc:
                self._record_issue(source, "document_preprocessing", exc)
                status_counts["failed"] += 1
                manifest_files[relative] = {"sha256": digest, "kind": "document", "status": "failed"}

        documents.sort(key=lambda item: item["source_path"])
        chunks.sort(key=lambda item: (item["source_path"], item["chunk_index"]))
        _write_jsonl(self.output_root / "documents.jsonl", documents)
        _write_jsonl(self.output_root / "chunks.jsonl", chunks)
        _write_jsonl(self.output_root / "errors.jsonl", (issue.to_dict() for issue in self.issues))

        now = datetime.now(timezone.utc).isoformat()
        manifest = {
            "version": 1,
            "pipeline_version": PIPELINE_VERSION,
            "generated_at": now,
            "dataset_root": str(self.dataset_root),
            "allowed_source_directories": list(ALLOWED_SOURCE_DIRECTORIES),
            "excluded_directories": list(EXCLUDED_DIRECTORIES),
            "files": manifest_files,
        }
        _atomic_write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

        source_type_counts = Counter(record["source_type"] for record in documents)
        document_type_counts = Counter(record["document_type"] for record in documents)
        report = {
            "completed_at": now,
            "source": str(self.dataset_root),
            "output": str(self.output_root),
            "structured_tables": len(structured_summary),
            "structured_rows": sum(item["rows"] for item in structured_summary.values()),
            "documents": len(documents),
            "chunks": len(chunks),
            "issues": len(self.issues),
            "statuses": dict(sorted(status_counts.items())),
            "source_types": dict(sorted(source_type_counts.items())),
            "document_types": dict(sorted(document_type_counts.items())),
            "structured": structured_summary,
            "excluded_directories": list(EXCLUDED_DIRECTORIES),
        }
        _atomic_write_text(
            self.output_root / "run_report.json",
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        return report

