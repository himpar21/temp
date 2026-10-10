"""Local PDF source connector."""

from __future__ import annotations

from pathlib import Path


def discover_pdfs(pdf_root: Path) -> list[Path]:
    if not pdf_root.exists():
        return []
    return sorted(path for path in pdf_root.rglob("*.pdf") if path.is_file())

