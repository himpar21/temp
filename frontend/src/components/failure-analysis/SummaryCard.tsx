import type { TestCase, Defect, FailureLog } from "../../types";

export default function SummaryCard({
  testCase,
  defect,
  log,
}: {
  testCase: TestCase;
  defect?: Defect;
  log?: FailureLog;
}) {
  const confidence = defect ? 0.81 : 0.62;
  return (
    <div className="rounded border border-line bg-surface p-4">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-medium text-slate">AI summary</span>
        <span className="rounded-full bg-accent-soft px-2 py-0.5 text-xs font-medium text-accent">
          Confidence {(confidence * 100).toFixed(0)}%
        </span>
      </div>
      <p className="text-sm leading-relaxed text-ink">
        {testCase.id} in <span className="font-medium">{testCase.module}</span> failed
        {log ? ` with "${log.message}"` : ""} on {testCase.environment}.
        {defect
          ? ` A ${defect.severity.toLowerCase()}-severity defect (${defect.id}) is already logged and currently ${defect.status.toLowerCase()}.`
          : " No defect has been logged for this failure yet."}
      </p>
    </div>
  );
}
