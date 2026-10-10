import type { Chunk } from "../../types";
import { FileText, Bug, ScrollText, FileUp } from "lucide-react";

const ICONS: Record<Chunk["sourceType"], typeof FileText> = {
  TestCase: FileText,
  Defect: Bug,
  Log: ScrollText,
  UploadedDocument: FileUp,
};

export default function ChunkCard({ chunk }: { chunk: Chunk }) {
  const Icon = ICONS[chunk.sourceType];
  return (
    <div className="rounded border border-line bg-surface p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-sm font-medium text-slate">
          <Icon size={12} />
          {chunk.sourceType} · {chunk.sourceId}
        </span>
        <span className="font-mono text-sm text-slate">{chunk.score.toFixed(2)}</span>
      </div>
      <p className="text-sm leading-relaxed text-ink">{chunk.text}</p>
      <div className="mt-2 h-1 w-full overflow-hidden rounded bg-accent-soft">
        <div
          className="h-full rounded bg-accent"
          style={{ width: `${Math.round(chunk.score * 100)}%` }}
        />
      </div>
    </div>
  );
}
