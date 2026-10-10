"""Heading-aware document chunk generation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import replace

from ingestion.models import DocumentChunk, SourceDocument


HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def _sections(text: str) -> list[tuple[str, str]]:
    matches = list(HEADING_PATTERN.finditer(text))
    if not matches:
        return [("Document", text)]
    sections: list[tuple[str, str]] = []
    prefix = text[: matches[0].start()].strip()
    if prefix:
        sections.append(("Document", prefix))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section_text = text[match.end() : end].strip()
        if section_text:
            sections.append((match.group(2).strip(), section_text))
    return sections


def _word_windows(text: str, max_words: int, overlap_words: int) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text.strip()] if text.strip() else []
    step = max_words - overlap_words
    return [" ".join(words[start : start + max_words]) for start in range(0, len(words), step)]


def generate_chunks(
    document: SourceDocument,
    max_words: int = 350,
    overlap_words: int = 50,
) -> list[DocumentChunk]:
    if max_words < 20:
        raise ValueError("max_words must be at least 20")
    if overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("overlap_words must be between 0 and max_words - 1")

    chunks: list[DocumentChunk] = []
    for section, section_text in _sections(document.text):
        for window in _word_windows(section_text, max_words, overlap_words):
            index = len(chunks)
            chunk_text = f"{section}\n\n{window}" if section != "Document" else window
            digest = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document.document_id}:{document.source_type}:{index:04d}",
                    document_id=document.document_id,
                    source_path=document.source_path,
                    document_type=document.document_type,
                    section=section,
                    chunk_index=index,
                    text=chunk_text,
                    metadata={**document.metadata, "section": section},
                    entity_ids=document.entity_ids,
                    content_hash=digest,
                )
            )
    return chunks

