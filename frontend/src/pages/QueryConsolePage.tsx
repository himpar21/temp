import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import QuestionInput from "../components/query-console/QuestionInput";
import AnswerCard from "../components/query-console/AnswerCard";
import RagTransparencyStrip from "../components/query-console/RagTransparencyStrip";
import { query } from "../api/mockClient";
import type { QueryResult } from "../types";
import { useHistory } from "../context/HistoryContext";
import { useRole } from "../context/RoleContext";

export default function QueryConsolePage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchParams] = useSearchParams();
  const { addToHistory } = useHistory();
  const { role } = useRole();
  const didRunFromParam = useRef(false);

  // Show transparency strip only for Admin and Test Lead
  const showTransparency = role === "Admin" || role === "Test Lead";

  async function handleAsk(q: string) {
    if (!q.trim()) return;
    setQuestion(q);
    setLoading(true);
    setResult(null);
    try {
      const res = await query(q, 5);
      setResult(res);
      addToHistory(q);
    } finally {
      setLoading(false);
    }
  }

  // Auto-run query if URL has ?q= param (from history click) — only once
  useEffect(() => {
    const q = searchParams.get("q");
    if (q && !didRunFromParam.current) {
      didRunFromParam.current = true;
      handleAsk(q);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Listen for "New Chat" event from sidebar
  useEffect(() => {
    function handleNewChat() {
      setQuestion("");
      setResult(null);
      didRunFromParam.current = false;
    }
    window.addEventListener("new-chat", handleNewChat);
    return () => window.removeEventListener("new-chat", handleNewChat);
  }, []);

  return (
    <div className={`mx-auto max-w-3xl space-y-5 ${!result && !loading ? "flex min-h-[70vh] flex-col justify-center" : "pt-8"}`}>
      {!result && !loading && (
        <h1 className="mb-8 text-center text-3xl font-semibold text-ink">
          What would you like to know?
        </h1>
      )}

      <QuestionInput onSubmit={handleAsk} loading={loading} />

      {!result && !loading && (
        <div className="mt-8 text-center text-sm text-slate">
          Pick a suggested prompt, or ask anything to see the retrieval pipeline in action.
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <AnswerCard question={question} answer={result.answer} />
          {showTransparency && (
            <RagTransparencyStrip
              vanillaScore={result.vanillaScore}
              chunks={result.chunks}
              retrievalSource={result.retrievalSource}
              decisionReason={result.decisionReason}
            />
          )}
        </div>
      )}
    </div>
  );
}
