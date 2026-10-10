# AI Test Management Backend

Backend service for AI-based test management, PostgreSQL-backed ingestion, preprocessing,
and graph-powered test execution insights.

## Dataset ingestion and preprocessing

The local ingestion pipeline reads only these primary source directories:

- `datasets/synthetic_test_management/structured/*.csv`
- `datasets/synthetic_test_management/unstructured/**/*.md`
- `datasets/synthetic_test_management/pdf_documents/**/*.pdf`

It intentionally excludes `graph/`, `evaluation/`, `input_fixtures/`, metadata,
generation scripts, and existing indexes. This prevents benchmark leakage and ensures
that later graph construction is based on ingested source records rather than the
precomputed reference graph.

Run the complete pipeline from the repository root:

```bash
python backend/scripts/ingest_documents.py
```

For a faster CSV and Markdown-only run:

```bash
python backend/scripts/ingest_documents.py --skip-pdfs
```

Generated artifacts are written to `backend/data/ingestion/`:

- `structured/*.csv`: cleaned, normalized, primary-key-deduplicated tables
- `documents.jsonl`: parsed documents with source metadata and extracted entity IDs
- `chunks.jsonl`: heading-aware overlapping chunks ready for embedding
- `manifest.json`: SHA-256 source catalog used for incremental reruns
- `run_report.json`: counts by table, document type, source type, and status
- `errors.jsonl`: per-file failures, including PDFs that require OCR

Use `--fail-on-error` in CI to make any malformed source fail the command. Without it,
the batch records the error and continues processing other artifacts.

## Automatic user-upload ingestion

Start PostgreSQL and the API:

```bash
docker compose up --build
```

Every upload to `POST /api/v1/ingestion/upload` immediately runs validation,
parsing/OCR where applicable, cleaning, exact-content deduplication, normalization,
metadata and entity-ID extraction, heading-aware chunking, and PostgreSQL persistence.

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/upload \
  -F "file=@sample.pdf"
```

Supported extensions are CSV, JSON, JSONL, Markdown, text, PDF, XLSX, DOCX, PNG,
JPG, and JPEG. The default upload limit is 25 MB. Image OCR uses Tesseract, which is
installed in the backend Docker image.

The upload response includes a job ID. Status and ingestion counts are available at:

```text
GET /api/v1/ingestion/jobs/{job_id}
```

PostgreSQL is the only artifact datastore:

- `structured_records`: normalized CSV/Excel/JSON records
- `documents`: parsed unstructured and structured source text
- `document_chunks`: preprocessed chunks ready for embedding
- `graph_nodes` and `graph_edges`: reserved for the downstream Graph RAG pipeline
- `ingestion_jobs`: processing, failure, and deduplication state

Upload ingestion does not create nodes, edges, or relationships. It stores entity IDs
as document/chunk metadata so the downstream Graph RAG pipeline can resolve entities,
generate relationships, and populate `graph_nodes` and `graph_edges`. The supplied
dataset `graph/` directory is never read by upload ingestion.

this ids the code for  backebd
## Structure

- `app/`: Application entrypoint.
- `api/`: API routes and dependencies.
- `core/`: Configuration, security, logging, and exception handling.
- `database/postgres/`: the single persistence layer for records, documents, chunks, and graph data.
- `models/`: Domain models.
- `schemas/`: Request and response schemas.
- `services/`: Business logic services.
- `ai_engine/`: Embeddings, vanilla RAG, graph RAG, hybrid RAG, and LLM orchestration.
- `ingestion/`: Connectors, parsers, and chunking.
- `tasks/`: Background and scheduled jobs.
- `evaluation/`: RAG and LLM evaluation metrics.
- `tests/`: Unit, integration, and performance tests.
- `scripts/`: Utility scripts.

## Vanilla RAG API

The local Vanilla RAG demo indexes the synthetic Samsung testing artifacts in
`data/samsung_testing_artifacts.json` when the first query is received. It uses
deterministic hash embeddings and exact cosine similarity, so it runs without an
external model or vector database.

Start the API from the `backend` directory:

```powershell
uvicorn app.main:app --reload
```

Query the retriever:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/rag/query `
  -ContentType "application/json" `
  -Body '{"query":"Why do Galaxy Buds disconnect after screen lock?","top_k":3}'
```

The response contains the query embedding, top-k chunks, cosine similarity and
relevance scores, source metadata, retrieval metrics, and assembled context.

## Hybrid RAG Planner API

The planner runs Vanilla RAG first and compares its top relevance score (`Sv`)
with a configurable threshold (`T`, default `0.30`). When `Sv >= T`, the Vanilla
context is selected for grounded LLM response generation.
When `Sv < T`, the planner runs the Graph RAG pipeline and selects its
relationship-aware context for grounded LLM response generation.

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/hybrid-rag/query `
  -ContentType "application/json" `
  -Body '{"query":"Why do Galaxy Buds disconnect after screen lock?","top_k":3,"threshold":0.30}'
```

This unified handler calculates the Vanilla RAG relevance score, compares it
with the request threshold, executes Graph RAG only when the score is below the
threshold, invokes the configured Ollama model with the selected context, and
returns the generated `answer` plus a `pipeline_trace`. The older `/plan` route
remains as a deprecated compatibility alias.

## Graph RAG API

Graph RAG builds a test-management knowledge graph from the local artifact
dataset. Its pipeline performs query preprocessing, entity recognition and
linking, graph-query generation, bounded multi-hop traversal, relationship-aware
path ranking, confidence scoring, and structured context generation.

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/graph-rag/query `
  -ContentType "application/json" `
  -Body '{"query":"Which feature is most unstable in SmartThings?","top_k":8,"max_hops":4}'
```

The response exposes linked entities, the generated Cypher representation,
ranked traversal paths, relationship strengths, graph confidence, retrieval
metrics, graph context, and the grounded LLM-generated `answer`.

The retriever uses an in-memory projection for deterministic low-latency traversal.
At API startup, the same idempotent graph projection is persisted to Neo4j for
inspection and production graph access. The frontend query console calls the
adaptive Hybrid RAG endpoint and displays either vector chunks or ranked graph
paths, according to the threshold decision.

Uploaded documents are dynamically projected into the graph during ingestion.
Recognized applications, components, requirements, test cases, executions,
failures, defects, reports, and their traceability relationships are persisted in
PostgreSQL and synchronized to Neo4j. Existing uploads are backfilled at API
startup, and Graph/Hybrid RAG loads the latest projection on every request, so a
new upload is queryable without restarting the service.
