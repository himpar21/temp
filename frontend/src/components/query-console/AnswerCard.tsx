import { Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function AnswerCard({ question, answer }: { question: string; answer: string }) {
  return (
    <div className="rounded border border-line bg-surface p-5">
      <p className="text-sm text-slate">{question}</p>
      <div className="mt-3 flex items-start gap-3">
        <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded bg-accent-soft text-accent">
          <Sparkles size={12} />
        </span>
        <div className="min-w-0 flex-1 text-base leading-relaxed text-ink">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ children }) => <h2 className="mb-3 text-xl font-semibold">{children}</h2>,
              h2: ({ children }) => <h3 className="mb-2 mt-5 text-lg font-semibold first:mt-0">{children}</h3>,
              h3: ({ children }) => <h4 className="mb-2 mt-4 font-semibold first:mt-0">{children}</h4>,
              h4: ({ children }) => <h5 className="mb-1 mt-3 font-semibold first:mt-0">{children}</h5>,
              p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
              ul: ({ children }) => <ul className="mb-3 list-disc space-y-1 pl-5">{children}</ul>,
              ol: ({ children }) => <ol className="mb-3 list-decimal space-y-1 pl-5">{children}</ol>,
              li: ({ children }) => <li className="pl-1">{children}</li>,
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              hr: () => <hr className="my-4 border-line" />,
              table: ({ children }) => (
                <div className="mb-4 overflow-x-auto rounded border border-line">
                  <table className="w-full border-collapse text-sm">{children}</table>
                </div>
              ),
              th: ({ children }) => (
                <th className="border-b border-line bg-canvas px-3 py-2 text-left font-semibold">
                  {children}
                </th>
              ),
              td: ({ children }) => <td className="border-b border-line px-3 py-2">{children}</td>,
              code: ({ children }) => (
                <code className="rounded bg-canvas px-1.5 py-0.5 font-mono text-sm">{children}</code>
              ),
            }}
          >
            {answer}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
