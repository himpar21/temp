import { useState, FormEvent } from "react";

const FIXED_QUESTIONS = [
  "Which feature is most unstable in SmartThings?",
  "What defects are related to pairing failures?",
  "Which requirements have no test coverage?",
  "What is causing Bixby voice command failures?",
];

export default function ExperimentForm({
  onRun,
  running,
}: {
  onRun: (config: { question: string; threshold: number; topK: number }) => void;
  running: boolean;
}) {
  const [question, setQuestion] = useState(FIXED_QUESTIONS[0]);
  const [topK, setTopK] = useState(5);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onRun({ question, threshold: 0.3, topK });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 rounded border border-line bg-surface p-4">
      <div className="flex flex-col gap-1">
        <label className="text-xs text-slate">Question</label>
        <select
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="w-72 rounded border border-line bg-surface px-2 py-1.5 text-xs text-ink focus:outline-none focus:ring-1 focus:ring-accent"
        >
          {FIXED_QUESTIONS.map((q) => (
            <option key={q} value={q}>
              {q}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-xs text-slate">Top-K</label>
        <input
          type="number"
          min={1}
          max={20}
          value={topK}
          onChange={(e) => setTopK(Number(e.target.value))}
          className="w-20 rounded border border-line bg-surface px-2 py-1.5 text-xs text-ink focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>
      <button
        type="submit"
        disabled={running}
        className="rounded bg-accent px-4 py-1.5 text-xs font-medium text-white disabled:opacity-50"
      >
        {running ? "Running…" : "Run"}
      </button>
    </form>
  );
}
