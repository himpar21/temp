import { useState } from "react";
import ExperimentForm from "../components/experiments/ExperimentForm";
import ResultsComparisonTable from "../components/experiments/ResultsComparisonTable";
import { evaluate } from "../api/mockClient";
import type { ExperimentRun } from "../types";

export default function ExperimentsPage() {
  const [runs, setRuns] = useState<ExperimentRun[]>([]);
  const [running, setRunning] = useState(false);

  async function handleRun(config: { question: string; threshold: number; topK: number }) {
    setRunning(true);
    try {
      const res = await evaluate(config.question, { threshold: config.threshold, topK: config.topK });
      const run: ExperimentRun = {
        id: `run-${Date.now()}`,
        question: config.question,
        threshold: config.threshold,
        topK: config.topK,
        score: res.score,
        passed: res.passed,
        timestamp: new Date().toISOString(),
      };
      setRuns((prev) => [run, ...prev]);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-5">
      <ExperimentForm onRun={handleRun} running={running} />
      <ResultsComparisonTable runs={runs} />
    </div>
  );
}
