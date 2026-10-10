"""Regression tests for source isolation and preprocessing behavior."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from ingestion.chunking.chunk_generator import generate_chunks
from ingestion.parsers.document_parser import parse_markdown
from ingestion.preprocessing import infer_primary_entity_id, preprocess_query, repair_mojibake
from services.ingestion_service import IngestionService
from services.upload_ingestion_service import UploadIngestionService
from services.query_service import lexical_score


class IngestionPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.dataset = self.root / "dataset"
        self.output = self.root / "output"
        for name in ("structured", "unstructured/failure_logs", "graph", "evaluation", "input_fixtures"):
            (self.dataset / name).mkdir(parents=True, exist_ok=True)

        with (self.dataset / "structured" / "test_cases.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.writer(handle)
            writer.writerow(["test_case_id", "title"])
            writer.writerow(["TC-0001", " Bluetooth reconnects "])
            writer.writerow(["TC-0001", "duplicate"])

        (self.dataset / "unstructured" / "failure_logs" / "FAIL-0001.md").write_text(
            """---
document_id: FAIL-0001
document_type: failure_log
test_case_id: TC-0001
---
# Failure
## Root Cause
The Bluetooth service failed for `TC-0001` because the connection timed out.
""",
            encoding="utf-8",
        )
        for excluded in ("graph", "evaluation", "input_fixtures"):
            (self.dataset / excluded / "DO-NOT-INGEST.md").write_text(
                "SECRET-BENCHMARK-ANSWER", encoding="utf-8"
            )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_pipeline_excludes_benchmark_and_graph_directories(self) -> None:
        report = IngestionService(self.dataset, self.output, include_pdfs=False).run()
        self.assertEqual(report["structured_rows"], 1)
        self.assertEqual(report["documents"], 1)
        self.assertEqual(report["issues"], 0)

        documents = (self.output / "documents.jsonl").read_text(encoding="utf-8")
        chunks = (self.output / "chunks.jsonl").read_text(encoding="utf-8")
        manifest = (self.output / "manifest.json").read_text(encoding="utf-8")
        self.assertNotIn("SECRET-BENCHMARK-ANSWER", documents + chunks)
        self.assertNotIn("DO-NOT-INGEST", manifest)

    def test_second_run_reuses_unchanged_artifacts(self) -> None:
        service = IngestionService(self.dataset, self.output, include_pdfs=False)
        service.run()
        report = service.run()
        self.assertEqual(report["statuses"].get("unchanged"), 2)
        self.assertEqual(report["issues"], 0)

    def test_metadata_entities_and_heading_chunks(self) -> None:
        path = self.dataset / "unstructured" / "failure_logs" / "FAIL-0001.md"
        document = parse_markdown(path, self.dataset)
        chunks = generate_chunks(document, max_words=20, overlap_words=5)
        self.assertEqual(document.document_id, "FAIL-0001")
        self.assertEqual(document.entity_ids, ["FAIL-0001", "TC-0001"])
        self.assertTrue(any(chunk.section == "Root Cause" for chunk in chunks))

    def test_query_validation_and_encoding_repair(self) -> None:
        self.assertEqual(preprocess_query("  why   did TC-0001 fail?  "), "why did TC-0001 fail?")
        self.assertEqual(repair_mojibake("Failure â€” timeout"), "Failure — timeout")
        with self.assertRaises(ValueError):
            preprocess_query("   ")

    def test_pdf_primary_entity_comes_from_filename(self) -> None:
        entity_ids = ["APP-004", "BUG-0007", "REQ-0303"]
        self.assertEqual(
            infer_primary_entity_id(Path("defect_bug_0007.pdf"), entity_ids),
            "BUG-0007",
        )
        self.assertEqual(
            infer_primary_entity_id(Path("plan_ts_0108.pdf"), ["APP-001", "TS-0108"]),
            "TS-0108",
        )

    def test_upload_csv_is_normalized_and_deduplicated(self) -> None:
        service = UploadIngestionService(session=None)  # extraction is database-independent
        text, metadata, records = service._extract(
            "cases.csv",
            ".csv",
            b"test_case_id,title\nTC-0001, Login test \nTC-0001, Login test \n",
        )
        self.assertEqual(metadata["document_type"], "structured_csv")
        self.assertEqual(metadata["columns"], ["test_case_id", "title"])
        self.assertEqual(records, [{"test_case_id": "TC-0001", "title": "Login test"}])
        self.assertIn("TC-0001", text)

    def test_upload_markdown_front_matter_is_extracted(self) -> None:
        service = UploadIngestionService(session=None)
        text, metadata, records = service._extract(
            "failure.md",
            ".md",
            b"---\ndocument_id: FAIL-0001\ndocument_type: failure_log\n---\n# Failure\nTimeout",
        )
        self.assertEqual(metadata["document_id"], "FAIL-0001")
        self.assertEqual(metadata["document_type"], "failure_log")
        self.assertIn("Timeout", text)
        self.assertEqual(records, [])

    def test_query_scoring_prefers_matching_uploaded_content(self) -> None:
        resume = "Tannu Suman is an AI/ML Research Intern working on retrieval pipelines."
        unrelated = "Bluetooth device pairing failed in the SmartThings test suite."
        self.assertEqual(lexical_score("who is Tannu Suman", resume), 1.0)
        self.assertEqual(lexical_score("who is Tannu Suman", unrelated), 0.0)


if __name__ == "__main__":
    unittest.main()
