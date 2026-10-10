"""Cleaning, normalization, metadata extraction, and query preprocessing."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path
from typing import Any


ENTITY_PATTERN = re.compile(
    r"\b(?:DR-BUG|TP-TS|APP|SOL|REQ|TS|TC|EXEC|FAIL|BUG|DEF|REPORT|LOG|RUN|ENV|REL|ENG|STEP)-[A-Z0-9][A-Z0-9-]*\b",
    re.IGNORECASE,
)
MOJIBAKE_MARKERS = ("â€", "â†", "â‰", "Ã", "Â")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def repair_mojibake(value: str) -> str:
    """Repair common UTF-8-as-Windows-1252 corruption without altering valid text."""
    if not any(marker in value for marker in MOJIBAKE_MARKERS):
        return value
    try:
        repaired = value.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value
    old_score = sum(value.count(marker) for marker in MOJIBAKE_MARKERS)
    new_score = sum(repaired.count(marker) for marker in MOJIBAKE_MARKERS)
    return repaired if new_score < old_score else value


def clean_text(value: str) -> str:
    value = repair_mojibake(value.replace("\x00", ""))
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+$", "", line) for line in value.split("\n")]
    result: list[str] = []
    blank = False
    for line in lines:
        is_blank = not line.strip()
        if is_blank and blank:
            continue
        result.append(line)
        blank = is_blank
    return "\n".join(result).strip()


def normalize_scalar(value: str) -> str:
    value = clean_text(value)
    return re.sub(r"[ \t]+", " ", value).strip()


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Parse the dataset's simple YAML front matter without a YAML dependency."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, text

    metadata: dict[str, Any] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = re.sub(r"[^a-z0-9_]+", "_", key.strip().lower()).strip("_")
        value = normalize_scalar(raw_value).strip("\"'")
        if key:
            metadata[key] = value
    return metadata, "\n".join(lines[end + 1 :]).strip()


def extract_entity_ids(text: str, metadata: dict[str, Any] | None = None) -> list[str]:
    combined = text
    if metadata:
        combined += "\n" + "\n".join(str(value) for value in metadata.values())
    return sorted({match.upper() for match in ENTITY_PATTERN.findall(combined)})


def infer_document_type(path: Path, metadata: dict[str, Any]) -> str:
    if metadata.get("document_type"):
        return str(metadata["document_type"]).lower()
    parent = path.parent.name.lower()
    return parent[:-1] if parent.endswith("s") else parent


def infer_primary_entity_id(path: Path, entity_ids: list[str]) -> str:
    """Infer the PDF's primary entity from the generator's stable filename format."""
    stem = path.stem.lower()
    patterns = (
        (r"^defect_bug_(\d+)$", "BUG-{0}"),
        (r"^fail_fail_(\d+)$", "FAIL-{0}"),
        (r"^req_req_(\d+)$", "REQ-{0}"),
        (r"^tc_tc_(\d+)$", "TC-{0}"),
        (r"^exec_exec_(\d+)$", "EXEC-{0}"),
        (r"^plan_ts_(\d+)$", "TS-{0}"),
    )
    for pattern, template in patterns:
        match = re.match(pattern, stem)
        if match:
            return template.format(match.group(1))
    return entity_ids[0] if entity_ids else path.stem


def preprocess_query(query: str, max_length: int = 4000) -> str:
    """Validate and normalize a natural-language query without destroying meaning."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    query = normalize_scalar(query)
    if not query:
        raise ValueError("query must not be empty")
    if len(query) > max_length:
        raise ValueError(f"query exceeds {max_length} characters")
    return query
