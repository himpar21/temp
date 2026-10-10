# PDF Generation — README

This directory contains the deterministic synthetic PDF generation pipeline
for the AI-Powered Test Management System Hybrid RAG research project.

---

## Why This PDF Dataset Exists

The Hybrid RAG pipeline must handle three user-input modes:

1. **LINE ONLY** — natural-language query, no document
2. **PDF ONLY** — user uploads a PDF, no query
3. **LINE + PDF** — user asks a question *about* an uploaded PDF

To benchmark and evaluate all three modes, we need a realistic corpus of
PDF documents that map to the existing structured dataset.  These PDFs are
entirely synthetic — no real Samsung confidential data is included.

---

## Files in This Directory

| File | Purpose |
|------|---------|
| `generate_pdfs.py` | Main generator — creates all PDFs, fixtures, evaluation data |
| `data_loader.py` | Loads structured CSVs from the base dataset branch or disk |
| `relationship_resolver.py` | Hydrates rich context dicts from entity relationships |
| `templates.py` | ReportLab PDF templates for all six document types |
| `validate_pdf_dataset.py` | 16-check validator — run after generation |
| `README.md` | This file |

---

## Output Structure

```
datasets/synthetic_test_management/
├── pdf_documents/
│   ├── requirements/        40 requirement spec PDFs
│   ├── test_plans/          30 test plan PDFs
│   ├── test_cases/          50 test case spec PDFs
│   ├── execution_reports/   40 execution report PDFs
│   ├── failure_reports/     50 failure analysis PDFs
│   └── defect_reports/      40 defect report PDFs
│
├── pdf_metadata/
│   ├── pdf_manifest.csv         One row per PDF with entity refs
│   └── pdf_entity_mapping.json  Explicit entity + relationship map per PDF
│
├── input_fixtures/
│   ├── line_only/               100 line-only query fixtures
│   ├── pdf_only/                50 PDF-only extraction fixtures
│   └── line_plus_pdf/           150 combined query + PDF fixtures
│
└── evaluation/
    └── pdf_input_evaluation/
        ├── questions.jsonl              300 evaluation queries
        ├── ground_truth.jsonl           300 expected answers
        ├── expected_entities.jsonl      300 entity sets
        ├── expected_relationships.jsonl 300 relationship sets
        └── evaluation_metrics.md        Metric definitions
```

---

## How PDFs Map to Existing Entities

Every PDF is generated from real entity IDs in the structured dataset.
The traceability chain is:

```
REQUIREMENT (REQ-NNNN)
    |
    +-- TEST CASE (TC-NNNN)          [IMPLEMENTS]
            |
            +-- TEST EXECUTION (EXEC-NNNNN) [HAS_EXECUTION]
                    |
                    +-- FAILURE (FAIL-NNNN)  [PRODUCED]
                            |
                            +-- DEFECT (BUG-NNNN)  [LINKED_TO]
                                    |
                                    +-- REQUIREMENT  [AFFECTS]
```

PDFs cross-reference actual IDs — a failure report PDF contains the real
`FAIL-xxxx`, `EXEC-xxxx`, `TC-xxxx`, `REQ-xxxx`, and `BUG-xxxx` IDs.

---

## How to Regenerate PDFs

```bash
# From repo root, activate the venv first
.venv/Scripts/activate   # Windows
# or
source .venv/bin/activate  # Linux/macOS

python datasets/synthetic_test_management/pdf_generation/generate_pdfs.py
```

Requires: `reportlab>=4.2.5` (install with `pip install reportlab==4.2.5`)

All output is deterministic — running twice with the same dataset and
`SEED=42` produces equivalent documents.

---

## How to Validate

```bash
python datasets/synthetic_test_management/pdf_generation/validate_pdf_dataset.py
```

Runs 16 checks covering:
- PDF file existence and readability
- Entity reference integrity
- No duplicate IDs
- All three input modes present
- All six document categories present
- Evaluation ground truth completeness
- Existing dataset files unmodified

---

## Input Modes Explained

### LINE ONLY
User sends a natural-language query. No PDF attached.
The system uses vector retrieval + graph traversal to answer.

Example: *"Which requirements are affected by failures in RUN-005?"*

### PDF ONLY
User uploads a PDF without a query.
The system extracts entities, relationships, and facts from the document.

Example: Upload `fail_fail_0042.pdf` → extract FAIL-0042, TC-xxxx, BUG-xxxx

### LINE + PDF
User uploads a PDF *and* asks a question about it.
This is the most important mode — requires both semantic PDF retrieval
and graph-based structured lookup.

Example: *"Does the failure in this report correspond to any historical failure?"*
         + `fail_fail_0042.pdf`

---

## Difference Between Dataset Generation and Application PDF Ingestion

| This PR | Future Application Work |
|---------|------------------------|
| Creates synthetic PDFs for evaluation | Implements real PDF ingestion pipeline |
| Writes fixture JSONL files | Integrates with FastAPI upload endpoint |
| Produces ground-truth answers | Invokes actual RAG pipeline |
| Validates entity consistency | Processes user-uploaded PDFs at runtime |

**This PR does NOT implement the application PDF ingestion pipeline.**

---

## How Fixtures Benchmark RAG Modes

```
LINE_ONLY fixtures    → benchmark Vanilla RAG + Graph RAG
PDF_ONLY fixtures     → benchmark PDF extraction + chunking quality
LINE_PLUS_PDF fixtures→ benchmark the full Hybrid RAG pipeline
```

The `evaluation/pdf_input_evaluation/` directory provides ground truth
for all three modes so you can compute:

- Recall@k, Precision@k, MRR (retrieval)
- Entity extraction recall/precision (PDF understanding)
- Answer faithfulness, completeness, BERTScore (generation)

---

## Synthetic Data Disclaimer

All PDFs and fixtures are entirely synthetic.
No real Samsung internal documents, employee names, credentials,
internal URLs, or confidential information is included.
This dataset is intended solely for AI/RAG research and development.
