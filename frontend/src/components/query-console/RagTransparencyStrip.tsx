import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import ChunkCard from "./ChunkCard";
import type { Chunk } from "../../types";

export default function RagTransparencyStrip({
  vanillaScore,
  chunks,
  retrievalSource,
  decisionReason,
}: {
  vanillaScore: number;
  chunks: Chunk[];
  retrievalSource: "vanilla_rag" | "graph_rag";
  decisionReason: string;
}) {
  const [open, setOpen] = useState(true);
  const passed = retrievalSource === "vanilla_rag";
  const sourceLabel = retrievalSource === "graph_rag"
    ? "Graph RAG"
    : passed
      ? "Vanilla RAG — sufficient"
      : "Vanilla RAG fallback";

  return (
    <div className="rounded border border-line bg-surface">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-3"
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-slate">How this answer was found</span>
          <span
            className={`rounded-full px-2 py-0.5 text-sm font-medium ${
              passed ? "bg-pass/10 text-pass" : "bg-warn/10 text-warn"
            }`}
          >
            {sourceLabel}
          </span>
        </div>
        {open ? <ChevronUp size={14} className="text-slate" /> : <ChevronDown size={14} className="text-slate" />}
      </button>

      {open && (
        <div className="space-y-4 border-t border-line px-4 py-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-4 text-sm">
              <span className="text-slate">
                Vanilla RAG score{" "}
                <span className="font-mono text-ink">{vanillaScore.toFixed(2)}</span>
              </span>
              <div className="h-1 w-28 overflow-hidden rounded bg-accent-soft">
                <div
                  className="h-full rounded bg-accent"
                  style={{ width: `${Math.round(vanillaScore * 100)}%` }}
                />
              </div>
            </div>
          </div>

          {!passed && (
            <p className="rounded bg-warn/10 px-3 py-2 text-sm text-warn">
              {decisionReason}
            </p>
          )}

          <div className="space-y-2">
            <p className="text-sm font-medium text-slate">
              {retrievalSource === "graph_rag" ? "Retrieved graph paths" : "Retrieved chunks"}
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {chunks.map((c) => (
                <ChunkCard key={c.id} chunk={c} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
