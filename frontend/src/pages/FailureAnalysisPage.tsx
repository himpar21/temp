import { useMemo, useState } from "react";
import FailedTestPicker from "../components/failure-analysis/FailedTestPicker";
import SummaryCard from "../components/failure-analysis/SummaryCard";
import SimilarFailuresList from "../components/failure-analysis/SimilarFailuresList";
import {
  getFailedTestCases,
  getDefectForTestCase,
  getFailureLogForTestCase,
  getSimilarFailures,
} from "../api/mockClient";

export default function FailureAnalysisPage() {
  const failedCases = useMemo(() => getFailedTestCases(), []);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selected = failedCases.find((t) => t.id === selectedId) ?? null;
  const defect = selectedId ? getDefectForTestCase(selectedId) : undefined;
  const log = selectedId ? getFailureLogForTestCase(selectedId) : undefined;
  const similar = selectedId ? getSimilarFailures(selectedId) : [];

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <FailedTestPicker testCases={failedCases} selectedId={selectedId} onSelect={setSelectedId} />

      {!selected && (
        <div className="rounded border border-dashed border-line px-6 py-10 text-center text-sm text-slate">
          Pick a failed test case to see an AI-style summary and similar past failures.
        </div>
      )}

      {selected && (
        <div className="space-y-4">
          <SummaryCard testCase={selected} defect={defect} log={log} />
          <div>
            <p className="mb-2 text-xs font-medium text-slate">Similar past failures</p>
            <SimilarFailuresList items={similar} />
          </div>
        </div>
      )}
    </div>
  );
}
