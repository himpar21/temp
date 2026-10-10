import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";
import FileDropzone from "../components/upload/FileDropzone";
import { upload } from "../api/mockClient";

export default function UploadPage() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<{
    rowsProcessed: number;
    chunks: number;
    graphNodes: number;
    graphEdges: number;
  } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFile(selectedFile: File) {
    setFile(selectedFile);
    setResult(null);
    setError(null);
  }

  async function handleConfirm() {
    if (!file) return;
    setSubmitting(true);
    setError(null);
    try {
      const response = await upload(file);
      setResult({
        rowsProcessed: response.rowsProcessed,
        chunks: response.chunks,
        graphNodes: response.graphNodes,
        graphEdges: response.graphEdges,
      });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["records"] }),
        queryClient.invalidateQueries({ queryKey: ["structured-tables"] }),
        queryClient.invalidateQueries({ queryKey: ["unstructured-documents"] }),
      ]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Upload failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <FileDropzone onFile={handleFile} />

      {file && (
        <div>
          <button
            onClick={handleConfirm}
            disabled={submitting}
            className="rounded bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {submitting ? "Processing…" : "Upload and process"}
          </button>
        </div>
      )}

      {result && (
        <div className="flex items-center gap-2 rounded border border-pass/30 bg-pass/10 px-4 py-3 text-sm text-pass">
          <CheckCircle2 size={16} />
          Uploaded {file?.name}. Created {result.chunks} chunks, {result.graphNodes} graph
          nodes, and {result.graphEdges} graph relationships
          {result.rowsProcessed ? ` from ${result.rowsProcessed} structured records` : ""}.
        </div>
      )}

      {error && (
        <div className="rounded border border-fail/30 bg-fail/10 px-4 py-3 text-sm text-fail">
          {error}
        </div>
      )}
    </div>
  );
}
