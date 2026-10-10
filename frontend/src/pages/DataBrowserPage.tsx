import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import DataTable from "../components/data-browser/DataTable";
import FilterBar from "../components/data-browser/FilterBar";
import {
  getStructuredRecords,
  getStructuredTables,
  getUnstructuredDocuments,
} from "../api/mockClient";
import type { UploadedDocument } from "../types";

const CATEGORY_ALIASES: Record<string, string> = {
  defect: "defects",
  defect_report: "defects",
  defect_reports: "defects",
  execution_report: "test_executions",
  execution_reports: "test_executions",
  failure_log: "failures",
  failure_logs: "failures",
  release_note: "releases",
  release_notes: "releases",
  requirement: "requirements",
  test_case: "test_cases",
  test_plan: "test_plans",
};

const KNOWN_DOCUMENT_CATEGORIES = new Set([
  "defects",
  "failures",
  "project_documentation",
  "releases",
  "requirements",
  "test_cases",
  "test_executions",
  "test_plans",
  "troubleshooting",
]);

function canonicalCategory(value: string) {
  const normalized = value.trim().toLowerCase().replace(/[\s-]+/g, "_");
  return CATEGORY_ALIASES[normalized] ?? normalized;
}

function categoryFromDocument(document: UploadedDocument) {
  const parts = document.sourcePath.replace(/\\/g, "/").split("/");
  const folder = parts[0] === "unstructured" && parts.length > 1 ? parts[1] : document.documentType;
  const category = canonicalCategory(folder);
  return KNOWN_DOCUMENT_CATEGORIES.has(category) ? category : "others";
}

function humanize(value: string) {
  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function renderValue(value: unknown) {
  if (value == null || value === "") return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export default function DataBrowserPage() {
  const [category, setCategory] = useState("applications");
  const [search, setSearch] = useState("");

  const { data: structuredTables = [] } = useQuery({
    queryKey: ["structured-tables"],
    queryFn: getStructuredTables,
  });
  const { data: unstructuredDocuments = [] } = useQuery({
    queryKey: ["unstructured-documents"],
    queryFn: getUnstructuredDocuments,
  });

  const categories = useMemo(() => {
    const keys = new Set(structuredTables.map((table) => canonicalCategory(table.recordType)));
    unstructuredDocuments.forEach((document) => keys.add(categoryFromDocument(document)));
    return [...keys]
      .sort((left, right) => {
        if (left === "others") return 1;
        if (right === "others") return -1;
        return humanize(left).localeCompare(humanize(right));
      })
      .map((key) => ({ key, label: humanize(key) }));
  }, [structuredTables, unstructuredDocuments]);

  const structuredTable = structuredTables.find(
    (table) => canonicalCategory(table.recordType) === category,
  );
  const categoryDocuments = useMemo(() => {
    const query = search.trim().toLowerCase();
    return unstructuredDocuments.filter((document) => {
      if (categoryFromDocument(document) !== category) return false;
      if (!query) return true;
      return [document.filename, document.documentType, ...document.entityIds]
        .join(" ")
        .toLowerCase()
        .includes(query);
    });
  }, [category, search, unstructuredDocuments]);

  const { data: structuredResult } = useQuery({
    queryKey: ["structured-records", structuredTable?.recordType, search],
    queryFn: () => getStructuredRecords(structuredTable!.recordType, search),
    enabled: Boolean(structuredTable),
  });

  const structuredColumns = useMemo<ColumnDef<Record<string, unknown>, unknown>[]>(
    () =>
      (structuredTable?.columns ?? []).map((column) => ({
        accessorKey: column,
        header: humanize(column),
        cell: (info) => renderValue(info.getValue()),
      })),
    [structuredTable],
  );

  const documentColumns: ColumnDef<UploadedDocument, unknown>[] = [
    { accessorKey: "filename", header: "Filename" },
    { accessorKey: "documentType", header: "Document Type", cell: (info) => humanize(info.getValue() as string) },
    {
      accessorKey: "entityIds",
      header: "Entities",
      cell: (info) => (info.getValue() as string[]).join(", ") || "—",
    },
    {
      accessorKey: "createdAt",
      header: "Ingested",
      cell: (info) => new Date(info.getValue() as string).toLocaleString(),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        <div className="flex flex-wrap gap-1 rounded border border-line bg-surface p-1">
          {categories.map((item) => (
            <button
              key={item.key}
              onClick={() => setCategory(item.key)}
              className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${
                category === item.key ? "bg-accent-soft text-accent" : "text-slate hover:text-ink"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm font-medium text-ink">{humanize(category)}</p>
          <FilterBar
            search={search}
            onSearchChange={setSearch}
            filters={[]}
            values={{}}
            onFilterChange={() => undefined}
          />
        </div>
      </div>

      {structuredTable && (
        <section className="space-y-2">
          <h2 className="text-xs font-medium uppercase tracking-wide text-slate">
            Structured records · {structuredTable.rowCount.toLocaleString()}
          </h2>
          <DataTable
            key={`structured-${category}`}
            data={structuredResult?.rows ?? []}
            columns={structuredColumns}
            totalRows={structuredResult?.total}
          />
        </section>
      )}

      {categoryDocuments.length > 0 && (
        <section className="space-y-2">
          <h2 className="text-xs font-medium uppercase tracking-wide text-slate">
            Unstructured documents · {categoryDocuments.length.toLocaleString()}
          </h2>
          <DataTable
            key={`unstructured-${category}`}
            data={categoryDocuments}
            columns={documentColumns}
          />
        </section>
      )}

      {!structuredTable && categoryDocuments.length === 0 && (
        <div className="rounded border border-line bg-surface px-3 py-8 text-center text-xs text-slate">
          No records match the current search.
        </div>
      )}
    </div>
  );
}
