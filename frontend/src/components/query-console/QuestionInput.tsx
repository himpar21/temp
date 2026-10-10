import { useState, FormEvent } from "react";
import { ArrowUp } from "lucide-react";

const SUGGESTED = [
  "Which feature is most unstable in SmartThings?",
  "What defects are related to pairing failures?",
  "Which requirements have no test coverage?",
];

export default function QuestionInput({
  onSubmit,
  loading,
}: {
  onSubmit: (question: string) => void;
  loading: boolean;
}) {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!value.trim() || loading) return;
    onSubmit(value.trim());
  }

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="relative w-full">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask about test coverage, failures, or defects…"
          className="w-full rounded-full border border-line bg-surface py-4 pl-6 pr-32 text-base text-ink placeholder:text-slate focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <button
          type="submit"
          disabled={loading || !value.trim()}
          className="absolute bottom-2 right-2 top-2 flex items-center justify-center gap-2 rounded-full bg-accent px-5 text-sm font-medium text-white transition-opacity disabled:opacity-40"
        >
          {loading ? "Thinking…" : "Ask"}
          {!loading && <ArrowUp size={16} />}
        </button>
      </form>
      <div className="flex flex-wrap justify-center gap-2">
        {SUGGESTED.map((q) => (
          <button
            key={q}
            onClick={() => setValue(q)}
            className="rounded-full border border-line px-3 py-1 text-sm text-slate hover:border-accent hover:text-accent"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
