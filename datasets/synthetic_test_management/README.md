# Synthetic Test Management Dataset

> **Disclaimer:** All data in this dataset is entirely synthetic.  
> No real Samsung internal documents, employee names, credentials, internal URLs,  
> production identifiers, or confidential information is included.  
> This dataset is created solely for AI/RAG research and development purposes.

---

## 1. Dataset Purpose

This dataset provides a complete, realistic synthetic representation of an enterprise software
testing ecosystem designed to support research and development of the
**AI-Powered Test Management System using Hybrid RAG Pipelines**.

It is specifically constructed to enable:

- **Vanilla RAG** — semantic retrieval over unstructured QA documents
- **Graph RAG** — multi-hop knowledge-graph traversal for traceability queries
- **Hybrid RAG** — combined semantic + graph evidence for complex AI-generated insights
- **Test execution analytics** — failure trend analysis, pass-rate tracking
- **Requirement-to-defect traceability** — end-to-end chain from REQ → TC → EXEC → FAIL → BUG
- **Evaluation** — 300 ground-truth queries to benchmark retrieval and answer quality

---

## 2. Dataset Architecture

```
Structured Data (CSV)
        │
        ▼
 PostgreSQL / Relational DB ──────────────────────┐
        │                                          │
        ▼                                          ▼
 Graph Builder ──► Knowledge Graph (Neo4j)    Vector DB (Qdrant)
                                     │              │
                              Graph RAG         Vanilla RAG
                                     │              │
                                     └──────┬───────┘
                                            ▼
                                       Hybrid RAG
                                            │
                                            ▼
                                    LLM (Gemini / GPT)
                                            │
                                            ▼
                               Test Execution Insights
```

---

## 3. Directory Structure

```
datasets/synthetic_test_management/
├── README.md                         ← This file
├── metadata/
│   ├── dataset_info.json             ← Dataset statistics and provenance
│   ├── data_dictionary.json          ← Field-level documentation for all tables
│   └── generation_config.json        ← Generator configuration and scale presets
│
├── structured/                       ← Relational CSV files
│   ├── applications.csv              (12 rows)
│   ├── solutions.csv                 (25 rows)
│   ├── environments.csv              (10 rows)
│   ├── releases.csv                  (8 rows)
│   ├── engineers.csv                 (100 rows)
│   ├── requirements.csv              (520 rows)
│   ├── test_suites.csv               (110 rows)
│   ├── test_cases.csv                (2,100 rows)
│   ├── test_steps.csv                (9,496 rows)
│   ├── test_runs.csv                 (12 rows)
│   ├── test_executions.csv           (5,200 rows)
│   ├── execution_steps.csv           (13,481 rows)
│   ├── failures.csv                  (1,100 rows)
│   ├── defects.csv                   (520 rows)
│   ├── assignments.csv               (2,100 rows)
│   └── historical_failures.csv       (2,100 rows)
│
├── graph/
│   ├── nodes.csv                     (9,717 nodes)
│   ├── relationships.csv             (24,657 relationships)
│   └── graph_schema.json             ← Node/edge type definitions
│
├── unstructured/                     ← Markdown documents (238 total)
│   ├── requirements/                 (40 docs)
│   ├── test_plans/                   (20 docs)
│   ├── test_cases/                   (40 docs)
│   ├── execution_reports/            (12 docs)
│   ├── failure_logs/                 (60 docs)
│   ├── defect_reports/               (50 docs)
│   ├── release_notes/                (8 docs)
│   ├── troubleshooting/              (5 docs)
│   └── project_documentation/        (3 docs)
│
├── evaluation/
│   ├── questions.jsonl               (300 queries)
│   ├── ground_truth.jsonl            (300 ground-truth answers)
│   ├── semantic_queries.jsonl        (100 semantic queries)
│   ├── graph_queries.jsonl           (100 graph queries)
│   ├── hybrid_queries.jsonl          (100 hybrid queries)
│   ├── expected_entities.jsonl       (300 expected entity sets)
│   ├── expected_relationships.jsonl  (200 expected graph paths)
│   └── evaluation_metrics.md         ← Metric definitions and targets
│
└── scripts/
    ├── generate_dataset.py           ← Generates structured CSVs + graph
    ├── generate_documents.py         ← Generates unstructured Markdown docs
    ├── generate_evaluation.py        ← Generates evaluation queries + GT
    └── validate_dataset.py           ← Validates all relational consistency
```

---

## 4. Structured Data

The structured data models a realistic relational test-management database.

### Entity Hierarchy

```
APPLICATION
    └── SOLUTION
    └── REQUIREMENT ──────────────────────────────┐
            └── TEST_CASE ──► TEST_SUITE           │
                    └── TEST_STEP                  │
                    └── TEST_EXECUTION             │
                            └── FAILURE ──► DEFECT ┘
                                               └── ENGINEER (assigned)
TEST_RUN ◄── TEST_EXECUTION
RELEASE  ◄── TEST_SUITE
ENVIRONMENT ◄── TEST_EXECUTION
```

### Key Relationships

| From | To | Relationship | Cardinality |
|------|----|-------------|-------------|
| Requirement | Test Case | 1:N — one req → many TCs | 1:N |
| Test Case | Test Execution | 1:N — one TC → many executions | 1:N |
| Test Execution | Failure | 1:0..1 — FAIL status has one failure | 1:0..1 |
| Failure | Defect | N:1 — multiple failures → one defect | N:1 |
| Defect | Requirement | N:1 — defect affects a requirement | N:1 |
| Test Run | Test Execution | 1:N — one run → many executions | 1:N |

### Data Quality

- All foreign keys resolve (verified by validate_dataset.py)
- Test run aggregate statistics match underlying execution records
- Realistic failure rate: ~20% FAIL, ~55% PASS, ~10% BLOCKED, ~15% SKIPPED/NOT_RUN
- Recurring root-cause clusters simulate real-world defect patterns

---

## 5. Unstructured Data

238 Markdown documents provide the text corpus for vector retrieval.

Each document:
- Contains realistic QA domain language (no lorem ipsum)
- Cross-references actual entity IDs from the structured data
- Is formatted with YAML front-matter for metadata extraction

### Document Types

| Type | Count | Example |
|------|-------|---------|
| Requirement specs | 40 | `requirements/REQ-0042.md` |
| Test plans | 20 | `test_plans/TP-TS-0001.md` |
| Test case specs | 40 | `test_cases/TCD-TC-0100.md` |
| Execution reports | 12 | `execution_reports/EXEC-RPT-RUN-001.md` |
| Failure logs | 60 | `failure_logs/FAIL-0001.md` |
| Defect reports | 50 | `defect_reports/DR-BUG-0001.md` |
| Release notes | 8 | `release_notes/RN-REL-001.md` |
| Troubleshooting guides | 5 | `troubleshooting/TS-BT-001.md` |
| Project documentation | 3 | `project_documentation/ARCH-001.md` |

---

## 6. Knowledge Graph

The graph captures the complete traceability network.

### Node Types (14)

`APPLICATION` · `SOLUTION` · `REQUIREMENT` · `TEST_SUITE` · `TEST_CASE` · `TEST_STEP` ·
`TEST_RUN` · `TEST_EXECUTION` · `FAILURE` · `DEFECT` · `ENGINEER` · `ENVIRONMENT` ·
`RELEASE` · `COMPONENT`

### Relationship Types (20)

`BELONGS_TO` · `IMPLEMENTS` · `COVERS` · `CONTAINS` · `EXECUTED_IN` · `EXECUTED_DURING` ·
`PRODUCED` · `CAUSED_BY` · `LINKED_TO` · `AFFECTS` · `ASSIGNED_TO` · `FIXED_BY` ·
`VERIFIED_BY` · `DEPENDS_ON` · `RELATED_TO` · `BLOCKS` · `REPRODUCES` · `OCCURRED_IN` ·
`PART_OF` · `HAS_EXECUTION`

### Multi-hop Example Paths

```
REQ-0001
  ←[IMPLEMENTS]←
    TC-0042
      →[HAS_EXECUTION]→
        EXEC-01234
          →[PRODUCED]→
            FAIL-0056
              →[LINKED_TO]→
                BUG-0031
                  →[AFFECTS]→
                    REQ-0001
```

This cycle is the foundation of the hybrid traceability queries.

---

## 7. Hybrid RAG Usage

The dataset is specifically designed so that the best answers require **both**:

1. **Semantic evidence** — text retrieved from `failure_logs/`, `defect_reports/`, `troubleshooting/`
2. **Graph evidence** — multi-hop traversal through the knowledge graph

### Example Hybrid Query

> *"Why did TC-0042 fail, which requirement does it affect, and has the same issue occurred before?"*

**Vanilla RAG alone** retrieves the failure log for FAIL-0056 — gives error details.  
**Graph RAG alone** traverses TC-0042 → EXEC → FAIL → BUG → REQ — gives traceability.  
**Hybrid RAG** combines both to answer: root cause + impact + historical recurrence.

---

## 8. Evaluation Dataset

### Query Types

| Type | Count | Purpose |
|------|-------|---------|
| `semantic` | 100 | Tests vector retrieval — failure analysis, troubleshooting, req descriptions |
| `graph` | 100 | Tests graph traversal — traceability chains, entity relationships |
| `hybrid` | 100 | Tests combined retrieval — requires both semantic and graph evidence |
| **Total** | **300** | |

### Evaluation Files

| File | Contents |
|------|----------|
| `questions.jsonl` | All 300 queries with query_id, question, type |
| `ground_truth.jsonl` | Expected answers + source entities + source documents |
| `expected_entities.jsonl` | Entity IDs that must be retrieved for each query |
| `expected_relationships.jsonl` | Graph paths that must be traversed |
| `evaluation_metrics.md` | Metric definitions and target thresholds |

---

## 9. Generation Process

All data is generated with a single deterministic seed (`SEED=42`) ensuring full reproducibility.

### Generation Order

```
1. generate_dataset.py     → structured CSVs + graph files
2. generate_documents.py   → unstructured Markdown documents (reads CSVs)
3. generate_evaluation.py  → evaluation queries (reads CSVs)
4. validate_dataset.py     → validates all consistency constraints
```

### To Regenerate from Scratch

```bash
cd datasets/synthetic_test_management/scripts

python generate_dataset.py
python generate_documents.py
python generate_evaluation.py
python validate_dataset.py
```

---

## 10. Validation Process

`validate_dataset.py` runs 15 checks:

| # | Check |
|---|-------|
| 1 | No duplicate IDs in any table |
| 2 | All foreign keys resolve |
| 3 | All graph relationships reference existing nodes |
| 4 | Every execution references an existing test case |
| 5 | Every failure references a valid execution |
| 6 | All defect references resolve |
| 7 | Every requirement referenced by a test case exists |
| 8 | Test run aggregates match underlying execution records |
| 9 | Every evaluation query has ground truth |
| 10 | Expected entities exist in the dataset |
| 11 | Expected relationships resolve in the graph |
| 12 | Unstructured documents reference valid entity IDs |
| 13 | No orphaned critical entities |
| 14 | Multi-hop graph paths are traversable |
| 15 | All required files are present |

---

## 11. How to Scale the Dataset

Edit the configuration constants in `generate_dataset.py`:

```python
SEED               = 42
NUM_APPLICATIONS   = 12
NUM_REQUIREMENTS   = 520
NUM_TEST_CASES     = 2100      # → change to 10000, 50000, 85000
NUM_TEST_EXECUTIONS = 5200     # → scale proportionally
NUM_FAILURES       = 1100
NUM_DEFECTS        = 520
```

Scale presets (defined in `generation_config.json`):

| Preset | Test Cases | Executions | Failures |
|--------|-----------|-----------|---------|
| demo | 2,100 | 5,200 | 1,100 |
| medium | 10,000 | 25,000 | 5,000 |
| large | 50,000 | 125,000 | 25,000 |
| xlarge | 85,000 | 200,000 | 40,000 |

> **Note:** Do not commit large-scale generated data to this repository.  
> Use the generator locally for scale testing.

---

## 12. Synthetic Data Disclaimer

This dataset is **entirely synthetic**. It was algorithmically generated using
Python with a fixed random seed for full reproducibility.

- All names, IDs, emails, and descriptions are fictional.
- No real Samsung internal data was used or referenced.
- No confidential information, credentials, API keys, or production identifiers are present.
- Application names (SmartHome, DigitalWallet, etc.) are illustrative labels for a
  fictional QA ecosystem and do not represent real Samsung products or internal systems.
- This dataset is intended solely for AI/RAG research and development purposes.

---

*Dataset version 1.0.0 — Generated 2024-09-26 — Seed 42*
