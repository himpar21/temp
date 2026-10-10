export interface Requirement {
  id: string;
  title: string;
  module: string;
  hasTestCoverage: boolean;
}

export type TestStatus = "Pass" | "Fail" | "Blocked" | "Not Run";
export type Environment = "Mobile" | "Watch" | "Hub" | "DA" | "Infra";

export interface TestCase {
  id: string;
  requirementId: string;
  module: string;
  description: string;
  steps: string[];
  status: TestStatus;
  lastRunAt: string;
  environment: Environment;
}

export type Severity = "Critical" | "High" | "Medium" | "Low";
export type DefectStatus = "Open" | "In Progress" | "Resolved";

export interface Defect {
  id: string;
  testCaseId: string;
  severity: Severity;
  status: DefectStatus;
  description: string;
  createdAt: string;
}

export interface FailureLog {
  id: string;
  testCaseId: string;
  message: string;
  timestamp: string;
}

export interface UploadedDocument {
  id: string;
  logicalDocumentId: string;
  filename: string;
  contentType: string | null;
  sourceType: string;
  documentType: string;
  sourcePath: string;
  entityIds: string[];
  createdAt: string;
}

export interface StructuredTableSummary {
  recordType: string;
  label: string;
  columns: string[];
  rowCount: number;
}

export interface StructuredTableData {
  recordType: string;
  columns: string[];
  total: number;
  rows: Record<string, unknown>[];
}

export type SourceType = "TestCase" | "Defect" | "Log" | "UploadedDocument";

export interface Chunk {
  id: string;
  sourceType: SourceType;
  sourceId: string;
  text: string;
  score: number;
}

export interface QueryResult {
  answer: string;
  vanillaScore: number;
  chunks: Chunk[];
  retrievalSource: "vanilla_rag" | "graph_rag";
  decisionReason: string;
}

export interface ExperimentRun {
  id: string;
  question: string;
  threshold: number;
  topK: number;
  score: number;
  passed: boolean;
  timestamp: string;
}
