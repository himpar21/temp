import type { ExperimentRun } from "../../types";

export default function ResultsComparisonTable({ runs }: { runs: ExperimentRun[] }) {
  if (runs.length === 0) {
    return (
      <div className="rounded border border-dashed border-line px-6 py-10 text-center text-sm text-slate">
        Run an experiment to compare scores across settings.
      </div>
    );
  }
  return (
    <div className="overflow-hidden rounded border border-line bg-surface">
      <table className="w-full text-left text-xs">
        <thead className="border-b border-line bg-paper">
          <tr>
            <th className="px-3 py-2 font-medium text-slate">Question</th>
            <th className="px-3 py-2 font-medium text-slate">Threshold</th>
            <th className="px-3 py-2 font-medium text-slate">Top-K</th>
            <th className="px-3 py-2 font-medium text-slate">Score</th>
            <th className="px-3 py-2 font-medium text-slate">Result</th>
            <th className="px-3 py-2 font-medium text-slate">Run at</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr key={r.id} className="border-b border-line last:border-0">
              <td className="max-w-xs truncate px-3 py-2 text-ink">{r.question}</td>
              <td className="px-3 py-2 font-mono text-ink">{r.threshold.toFixed(2)}</td>
              <td className="px-3 py-2 font-mono text-ink">{r.topK}</td>
              <td className="px-3 py-2 font-mono text-ink">{r.score.toFixed(2)}</td>
              <td className="px-3 py-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    r.passed ? "bg-pass/10 text-pass" : "bg-warn/10 text-warn"
                  }`}
                >
                  {r.passed ? "Vanilla RAG" : "Below threshold"}
                </span>
              </td>
              <td className="px-3 py-2 text-slate">{new Date(r.timestamp).toLocaleTimeString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
