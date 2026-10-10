// Mock API layer — the ONLY file that "knows" the data is synthetic.
// Every function here mirrors the shape a real backend endpoint would return
// (/query, /records, /upload, /evaluate). When the real Samsung dataset and
// RAG backend are ready, this file is the only one that needs to change.
import requirementsData from "./mockData/requirements.json";
import testCasesData from "./mockData/testCases.json";
import defectsData from "./mockData/defects.json";
import failureLogsData from "./mockData/failureLogs.json";
import type {
  Requirement,
  TestCase,
  Defect,
  FailureLog,
  Chunk,
  QueryResult,
  UploadedDocument,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

const requirements = requirementsData as Requirement[];
const testCases = testCasesData as TestCase[];
const defects = defectsData as Defect[];
const failureLogs = failureLogsData as FailureLog[];

function delay(ms = 250) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// --- naive lexical relevance scoring (stand-in for a real embedding search) ---
function tokenize(text: string): Set<string> {
  return new Set(
    text
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, " ")
      .split(/\s+/)
      .filter((w) => w.length > 2)
  );
}

function similarity(queryTokens: Set<string>, text: string): number {
  const textTokens = tokenize(text);
  if (textTokens.size === 0) return 0;
  let overlap = 0;
  queryTokens.forEach((t) => {
    if (textTokens.has(t)) overlap++;
  });
  if (overlap === 0) return 0;
  const denom = Math.sqrt(queryTokens.size * textTokens.size) || 1;
  return Math.min(1, overlap / denom + overlap * 0.08);
}

interface CorpusEntry {
  id: string;
  sourceType: Chunk["sourceType"];
  sourceId: string;
  text: string;
}

function buildCorpus(): CorpusEntry[] {
  const entries: CorpusEntry[] = [];
  testCases.forEach((tc) => {
    entries.push({
      id: `chunk-tc-${tc.id}`,
      sourceType: "TestCase",
      sourceId: tc.id,
      text: `${tc.module}: ${tc.description} (status: ${tc.status}, env: ${tc.environment})`,
    });
  });
  defects.forEach((d) => {
    entries.push({
      id: `chunk-def-${d.id}`,
      sourceType: "Defect",
      sourceId: d.id,
      text: `${d.description} (severity: ${d.severity}, status: ${d.status})`,
    });
  });
  failureLogs.forEach((l) => {
    const tc = testCases.find((t) => t.id === l.testCaseId);
    entries.push({
      id: `chunk-log-${l.id}`,
      sourceType: "Log",
      sourceId: l.id,
      text: `${tc ? tc.module : "Unknown module"}: ${l.message}`,
    });
  });
  return entries;
}

const corpus = buildCorpus();

function moduleFailureStats() {
  const byModule = new Map<string, { total: number; failed: number }>();
  testCases.forEach((tc) => {
    const entry = byModule.get(tc.module) ?? { total: 0, failed: 0 };
    entry.total += 1;
    if (tc.status === "Fail") entry.failed += 1;
    byModule.set(tc.module, entry);
  });
  return [...byModule.entries()]
    .map(([module, { total, failed }]) => ({
      module,
      total,
      failed,
      failRate: total ? failed / total : 0,
    }))
    .sort((a, b) => b.failRate - a.failRate);
}

function topKChunks(question: string, topK = 5): { chunks: Chunk[]; topScore: number } {
  const qTokens = tokenize(question);
  const scored = corpus
    .map((c) => ({ ...c, score: similarity(qTokens, c.text) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
  const topScore = scored.length ? scored[0].score : 0;
  return {
    chunks: scored.map((c) => ({
      id: c.id,
      sourceType: c.sourceType,
      sourceId: c.sourceId,
      text: c.text,
      score: Number(c.score.toFixed(2)),
    })),
    topScore,
  };
}

function synthesizeAnswer(question: string, topScore: number, chunks: Chunk[]): string {
  const q = question.toLowerCase();
  if (q.includes("unstable") || q.includes("most failures") || q.includes("flaky")) {
    const stats = moduleFailureStats().filter((s) => s.total >= 5);
    if (stats.length) {
      const top = stats[0];
      const pct = Math.round(top.failRate * 100);
      return `"${top.module}" has the highest failure rate at ${pct}% (${top.failed} of ${top.total} test cases failing). This is the module to prioritize for root-cause analysis.`;
    }
  }
  if (chunks.length === 0) {
    return "No sufficiently relevant test cases, defects, or logs were found for this question in the current dataset.";
  }
  const best = chunks[0];
  return `Based on the most relevant record (${best.sourceType} ${best.sourceId}, score ${best.score}): ${best.text}`;
}

export async function query(question: string, topK = 5): Promise<QueryResult> {
  // Try the real backend first; fall back to local mock if unavailable
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/hybrid-rag/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ query: question, top_k: topK }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      throw new Error(body?.detail ?? `Query failed (${response.status})`);
    }
    const result = (await response.json()) as {
      answer: string;
      decision: {
        vanilla_relevance_score: number;
        selected_source: "vanilla_rag" | "graph_rag";
        reason: string;
      };
      vanilla_candidates: Array<{
        chunk_id: string;
        artifact_id: string;
        artifact_type: string;
        title: string;
        content: string;
        similarity_score: number;
      }>;
      graph_result: null | {
        paths: Array<{
          rank: number;
          labels: string[];
          relationships: string[];
          score: number;
        }>;
      };
    };
    const chunks: Chunk[] = result.graph_result?.paths.length
      ? result.graph_result.paths.map((path) => ({
          id: `graph-path-${path.rank}`,
          sourceType: "UploadedDocument",
          sourceId: path.labels.join(" → "),
          text: path.labels
            .map((label, index) =>
              index < path.relationships.length
                ? `${label} -[${path.relationships[index]}]->`
                : label
            )
            .join(" "),
          score: path.score,
        }))
      : result.vanilla_candidates.map((chunk) => ({
          id: chunk.chunk_id,
          sourceType: "UploadedDocument",
          sourceId: chunk.title || chunk.artifact_id,
          text: chunk.content,
          score: chunk.similarity_score,
        }));
    return {
      answer: result.answer,
      vanillaScore: result.decision.vanilla_relevance_score,
      chunks,
      retrievalSource: result.decision.selected_source,
      decisionReason: result.decision.reason,
    };
  } catch (error) {
    if (error instanceof Error && !error.message.includes("Failed to fetch")) {
      throw error;
    }
    // Backend unavailable — use local mock data
    console.warn("[mockClient] Real backend unreachable, falling back to mock data.");
    await delay(400);
    const { chunks, topScore } = topKChunks(question, topK);
    const answer = synthesizeAnswer(question, topScore, chunks);
    return {
      answer,
      vanillaScore: Number(topScore.toFixed(2)),
      chunks,
      retrievalSource: "vanilla_rag",
      decisionReason: "The backend was unavailable, so local fallback data was used.",
    };
  }
}

export async function evaluate(
  question: string,
  settings: { threshold: number; topK: number }
): Promise<{ score: number; passed: boolean; chunks: Chunk[] }> {
  await delay(150);
  const { chunks, topScore } = topKChunks(question, settings.topK);
  return {
    score: Number(topScore.toFixed(2)),
    passed: topScore >= settings.threshold,
    chunks,
  };
}

export interface RecordFilters {
  entity: "uploads" | "testCases" | "defects" | "requirements" | "failureLogs";
  search?: string;
  module?: string;
  status?: string;
  environment?: string;
  severity?: string;
}

export async function getStructuredTables() {
  const response = await fetch(`${API_BASE_URL}/api/v1/ingestion/structured-tables`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error(`Unable to load structured datasets (${response.status})`);
  const tables = (await response.json()) as Array<{
    record_type: string;
    label: string;
    columns: string[];
    row_count: number;
  }>;
  return tables.map((table) => ({
    recordType: table.record_type,
    label: table.label,
    columns: table.columns,
    rowCount: table.row_count,
  }));
}

export async function getStructuredRecords(recordType: string, search?: string) {
  const params = new URLSearchParams({ limit: "1000" });
  if (search?.trim()) params.set("search", search.trim());
  const response = await fetch(
    `${API_BASE_URL}/api/v1/ingestion/structured-records/${encodeURIComponent(recordType)}?${params}`,
    { credentials: "include" },
  );
  if (!response.ok) throw new Error(`Unable to load ${recordType} records (${response.status})`);
  const result = (await response.json()) as {
    record_type: string;
    columns: string[];
    total: number;
    rows: Record<string, unknown>[];
  };
  return {
    recordType: result.record_type,
    columns: result.columns,
    total: result.total,
    rows: result.rows,
  };
}

export async function getUnstructuredDocuments() {
  const params = new URLSearchParams({ limit: "500" });
  const response = await fetch(`${API_BASE_URL}/api/v1/ingestion/documents?${params}`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error(`Unable to load unstructured documents (${response.status})`);
  const documents = (await response.json()) as Array<{
    id: string;
    logical_document_id: string;
    filename: string;
    content_type: string | null;
    source_type: string;
    document_type: string;
    source_path: string;
    entity_ids: string[];
    created_at: string;
  }>;
  const structuredSourceTypes = new Set(["csv", "json", "jsonl", "xlsx"]);
  return documents
    .filter((document) => !structuredSourceTypes.has(document.source_type))
    .map<UploadedDocument>((document) => ({
      id: document.id,
      logicalDocumentId: document.logical_document_id,
      filename: document.filename,
      contentType: document.content_type,
      sourceType: document.source_type,
      documentType: document.document_type,
      sourcePath: document.source_path,
      entityIds: document.entity_ids,
      createdAt: document.created_at,
    }));
}

export async function records(filters: RecordFilters) {
  if (filters.entity === "uploads") {
    const params = new URLSearchParams();
    if (filters.search?.trim()) params.set("search", filters.search.trim());
    const response = await fetch(`${API_BASE_URL}/api/v1/ingestion/documents?${params}`, {
      credentials: "include",
    });
    if (!response.ok) throw new Error(`Unable to load uploaded documents (${response.status})`);
    const documents = (await response.json()) as Array<{
      id: string;
      logical_document_id: string;
      filename: string;
      content_type: string | null;
      source_type: string;
      document_type: string;
      source_path: string;
      entity_ids: string[];
      created_at: string;
    }>;
    return documents.map<UploadedDocument>((document) => ({
      id: document.id,
      logicalDocumentId: document.logical_document_id,
      filename: document.filename,
      contentType: document.content_type,
      sourceType: document.source_type,
      documentType: document.document_type,
      sourcePath: document.source_path,
      entityIds: document.entity_ids,
      createdAt: document.created_at,
    }));
  }
  await delay(150);
  const search = filters.search?.toLowerCase().trim();

  if (filters.entity === "requirements") {
    return requirements.filter((r) => {
      if (filters.module && r.module !== filters.module) return false;
      if (search && !r.title.toLowerCase().includes(search) && !r.id.toLowerCase().includes(search)) return false;
      return true;
    });
  }
  if (filters.entity === "defects") {
    return defects.filter((d) => {
      if (filters.status && d.status !== filters.status) return false;
      if (filters.severity && d.severity !== filters.severity) return false;
      if (search && !d.description.toLowerCase().includes(search) && !d.id.toLowerCase().includes(search)) return false;
      return true;
    });
  }
  if (filters.entity === "failureLogs") {
    return failureLogs.filter((l) => {
      if (search && !l.message.toLowerCase().includes(search) && !l.testCaseId.toLowerCase().includes(search)) return false;
      return true;
    });
  }
  // testCases (default)
  return testCases.filter((tc) => {
    if (filters.module && tc.module !== filters.module) return false;
    if (filters.status && tc.status !== filters.status) return false;
    if (filters.environment && tc.environment !== filters.environment) return false;
    if (search && !tc.description.toLowerCase().includes(search) && !tc.id.toLowerCase().includes(search)) return false;
    return true;
  });
}

export async function upload(
  file: File,
): Promise<{
  success: boolean;
  rowsProcessed: number;
  chunks: number;
  graphNodes: number;
  graphEdges: number;
  jobId: string;
}> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE_URL}/api/v1/ingestion/upload`, {
    method: "POST",
    credentials: "include",
    body: form,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Upload failed (${response.status})`);
  }
  const result = (await response.json()) as {
    job_id: string;
    structured_records: number;
    chunks: number;
    graph_nodes: number;
    graph_edges: number;
  };
  return {
    success: true,
    rowsProcessed: result.structured_records,
    chunks: result.chunks,
    graphNodes: result.graph_nodes,
    graphEdges: result.graph_edges,
    jobId: result.job_id,
  };
}

export function getModules(): string[] {
  return [...new Set(testCases.map((t) => t.module))].sort();
}

export function getFailedTestCases(): TestCase[] {
  return testCases.filter((t) => t.status === "Fail");
}

export function getSimilarFailures(testCaseId: string, limit = 5) {
  const target = testCases.find((t) => t.id === testCaseId);
  if (!target) return [];
  const targetLog = failureLogs.find((l) => l.testCaseId === testCaseId);
  const qTokens = tokenize(`${target.module} ${targetLog?.message ?? ""}`);
  return testCases
    .filter((t) => t.status === "Fail" && t.id !== testCaseId)
    .map((t) => {
      const log = failureLogs.find((l) => l.testCaseId === t.id);
      const score = similarity(qTokens, `${t.module} ${log?.message ?? ""}`);
      return { testCase: t, log, score };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}

export function getDefectForTestCase(testCaseId: string) {
  return defects.find((d) => d.testCaseId === testCaseId);
}

export function getFailureLogForTestCase(testCaseId: string) {
  return failureLogs.find((l) => l.testCaseId === testCaseId);
}

export function moduleFailureRates() {
  return moduleFailureStats();
}
