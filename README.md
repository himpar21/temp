# Hybrid RAG for Test Execution Insights

An AI test management prototype that ingests test artifacts and answers questions using threshold-routed retrieval. The backend combines semantic search over uploaded chunks with graph traversal over test-management entities, then generates a grounded answer with a locally hosted Ollama model.

## Current implementation

- **API:** Python 3.11, FastAPI, Pydantic, SQLAlchemy
- **Web UI:** React 18, TypeScript, Vite, Tailwind CSS
- **Relational store:** PostgreSQL 16 for users, ingestion jobs, documents, chunks, and structured records
- **Vector search:** Qdrant for chunk embeddings and semantic retrieval
- **Knowledge graph:** Neo4j 5 Community for graph persistence; graph retrieval also loads the current projection in-process
- **Models:** Ollama `nomic-embed-text` embeddings and `qwen2.5-coder:1.5b` answer generation
- **Ingestion:** CSV, JSON/JSONL, Markdown, text, PDF, XLSX, DOCX, and common image uploads; PDF/document parsing and Tesseract OCR run in the backend container

The web UI is partially connected: query, upload, and uploaded-document browsing call the FastAPI API; some test case, defect, failure-log, and experiment views still use bundled synthetic mock data. The backend API can be used independently through its documented endpoints.

## Architecture

```text
React + Vite (5173)
       │ /api proxy
       ▼
FastAPI (8000) ───── Ollama on host (11434)
   ├── PostgreSQL (users, source records, chunks, jobs)
   ├── Qdrant (semantic chunk index)
   └── Neo4j (test-management graph)
```

Uploaded files are validated, parsed, normalized and chunked. PostgreSQL stores source content and ingestion state; chunks are embedded with Ollama and indexed in Qdrant. Recognized entities and relationships are projected into the graph and synchronized to Neo4j. A failed vector indexing step can be retried using the ingestion job endpoint.

For Hybrid RAG, the API first retrieves semantic candidates and compares the top relevance score (`Sv`) to `RAG_RELEVANCE_THRESHOLD` (default `0.85`). If `Sv >= T`, it uses the vector context. Otherwise, it retrieves graph paths and uses the graph context. The selected context is sent to Ollama for answer generation. The response includes the decision, candidates, selected context, graph result when used, and a pipeline trace.

## Run locally

### Prerequisites

- Docker Desktop with Docker Compose
- Node.js and npm
- Python 3.11 (only needed to run the backend outside Docker)
- [Ollama](https://ollama.com/) installed and running on the host

Pull the configured language and embedding models, then start Ollama:

```bash
ollama pull qwen2.5-coder:1.5b
ollama pull nomic-embed-text
ollama serve
```

In a separate terminal, start PostgreSQL, Qdrant, Neo4j, and the API from the backend directory:

```bash
cd backend
docker compose up --build
```

The compose file reads `backend/.env.example`. Its development credentials are for local use; change the secrets and database credentials before deployment. The API is available at `http://localhost:8000`, interactive OpenAPI docs at `http://localhost:8000/docs`, Qdrant at `http://localhost:6333/dashboard`, and Neo4j Browser at `http://localhost:7474`.

Start the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to `http://localhost:8000`; the browser session uses the API's HTTP-only authentication cookie. Create an account through the UI or `POST /api/v1/auth/signup` before using protected API routes.

To run the API directly instead of in Docker, start PostgreSQL, Qdrant, Neo4j, and Ollama separately, configure the service addresses in `backend/.env.example` (or the process environment), then run:

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API routes

Protected endpoints require a valid session cookie. Signup and login issue the cookie.

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/auth/signup` | Create an account and start a session |
| `POST` | `/api/v1/auth/login` | Start a session |
| `GET` | `/api/v1/auth/session` | Read the current session |
| `POST` | `/api/v1/auth/logout` | End the browser session |
| `POST` | `/api/v1/ingestion/upload` | Ingest and index an uploaded artifact |
| `GET` | `/api/v1/ingestion/jobs/{job_id}` | Read ingestion status and counts |
| `POST` | `/api/v1/ingestion/jobs/{job_id}/retry-indexing` | Retry vector indexing from stored chunks |
| `GET` | `/api/v1/ingestion/documents` | Browse ingested documents |
| `GET` | `/api/v1/ingestion/structured-tables` | List structured datasets |
| `GET` | `/api/v1/ingestion/structured-records/{record_type}` | Browse structured rows |
| `POST` | `/api/v1/rag/query` | Run semantic (Vanilla) RAG |
| `POST` | `/api/v1/graph-rag/query` | Run Graph RAG |
| `POST` | `/api/v1/hybrid-rag/query` | Run threshold-routed Hybrid RAG |
| `GET` | `/health` | Check API and dependency availability |

Example Hybrid RAG request (after authentication):

```bash
curl -X POST http://localhost:8000/api/v1/hybrid-rag/query \
  -H "Content-Type: application/json" \
  -b cookies.txt -c cookies.txt \
  -d '{"query":"Which test failures are linked to Bluetooth disconnects?","top_k":5}'
```

The `/api/v1/hybrid-rag/plan` route remains as a deprecated compatibility alias.

## Seed the repository dataset

The ingestion script processes the supported source directories under `datasets/synthetic_test_management/` and writes generated reports and intermediate data under `backend/data/ingestion/`:

```bash
python backend/scripts/ingest_documents.py
```

Skip PDF parsing for a faster CSV and Markdown run:

```bash
python backend/scripts/ingest_documents.py --skip-pdfs
```

This script prepares local ingestion artifacts. It is separate from the live upload API, which persists uploaded content and indexing state to the configured services.

## Repository map

```text
backend/
  app/                 FastAPI application and lifecycle
  api/routes/          Authentication, ingestion, and RAG endpoints
  ai_engine/           Embeddings, Vanilla RAG, Graph RAG, Hybrid planner, LLM
  database/            PostgreSQL, Qdrant, and Neo4j clients and models
  ingestion/           Parsers, preprocessing, and chunking
  services/             Upload processing and graph projection
  scripts/              Dataset ingestion and utility scripts
frontend/
  src/pages/            Query, upload, data, failure, and experiment screens
  src/api/              API client and synthetic mock data/fallbacks
datasets/
  synthetic_test_management/  Sample structured and unstructured source artifacts
```
