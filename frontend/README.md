# Test Insight — Frontend (Worklet 26SE08)

Frontend-only scaffold for the AI-powered test management system. Runs entirely
against a synthetic dataset behind a mock API layer — no backend required to
see it working.

## Run it locally

```bash
npm install
npm run dev
```

Then open the printed local URL (default http://localhost:5173).

## Regenerate the synthetic dataset

```bash
npm run generate-mock-data
```

This overwrites the JSON files in `src/api/mockData/` with a fresh, deterministic
synthetic dataset (25 requirements, ~250 test cases, defects, and failure logs,
with one deliberately unstable module so the RAG demo has a real answer).

## Where things live

- `src/api/mockClient.ts` — the ONLY file that needs to change when a real
  backend/RAG pipeline exists. Everything else calls its functions
  (`query`, `records`, `upload`, `evaluate`) and doesn't know the data is fake.
- `src/pages/` — the 5 routed pages: Query Console (`/`), Data Browser (`/data`),
  Upload Data (`/upload`), Failure Analysis (`/failure-analysis`), Experiments
  (`/experiments`).
- `src/components/` — page-specific components, grouped by page.
- `src/types/index.ts` — shared TypeScript interfaces for all entities.

## Notes

- Graph RAG is intentionally NOT implemented. When the Vanilla RAG score is
  below the threshold, the UI shows an honest "Graph RAG would run here — not
  available yet" message instead of faking a result.
- Dark mode toggle lives in the top bar.
- The Data Browser's table is built on TanStack Table with pagination so it
  stays responsive as row counts grow toward the real ~85k test cases.
