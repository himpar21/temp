import type { TestCase, FailureLog } from "../../types";

export default function SimilarFailuresList({
  items,
}: {
  items: { testCase: TestCase; log?: FailureLog; score: number }[];
}) {
  if (items.length === 0) {
    return <p className="text-xs text-slate">No similar past failures found.</p>;
  }
  return (
    <div className="space-y-2">
      {items.map(({ testCase, log, score }) => (
        <div key={testCase.id} className="flex items-center justify-between rounded border border-line bg-surface px-3 py-2">
          <div>
            <p className="text-xs font-medium text-ink">
              {testCase.id} · {testCase.module}
            </p>
            {log && <p className="font-mono text-xs text-slate">{log.message}</p>}
          </div>
          <span className="font-mono text-xs text-slate">{score.toFixed(2)}</span>
        </div>
      ))}
    </div>
  );
}
