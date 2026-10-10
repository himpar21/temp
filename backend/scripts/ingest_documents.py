"""Command-line entry point for dataset ingestion and preprocessing."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.ingestion_service import IngestionService  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest structured CSV, Markdown, and PDF source artifacts.",
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=REPOSITORY_ROOT / "datasets" / "synthetic_test_management",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=BACKEND_ROOT / "data" / "ingestion",
    )
    parser.add_argument("--skip-pdfs", action="store_true", help="Process CSV and Markdown only.")
    parser.add_argument("--max-chunk-words", type=int, default=350)
    parser.add_argument("--chunk-overlap-words", type=int, default=50)
    parser.add_argument("--fail-on-error", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    # Some generated PDFs have repairable cross-reference offsets. pypdf recovers
    # them successfully; avoid emitting one warning per file in normal batch runs.
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    service = IngestionService(
        args.dataset_root,
        args.output_root,
        include_pdfs=not args.skip_pdfs,
        max_chunk_words=args.max_chunk_words,
        chunk_overlap_words=args.chunk_overlap_words,
        fail_on_error=args.fail_on_error,
    )
    report = service.run()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["issues"] and args.fail_on_error else 0


if __name__ == "__main__":
    raise SystemExit(main())

