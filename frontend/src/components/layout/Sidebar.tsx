import { NavLink, useNavigate } from "react-router-dom";
import {
  MessageSquare,
  Table2,
  UploadCloud,
  SearchCode,
  FlaskConical,
  Plus,
  Clock,
  Trash2,
} from "lucide-react";
import { useHistory } from "../../context/HistoryContext";

const NAV_ITEMS = [
  { to: "/", label: "Query Console", icon: MessageSquare, end: true },
  { to: "/data", label: "Data Browser", icon: Table2 },
  { to: "/upload", label: "Upload Data", icon: UploadCloud },
  { to: "/failure-analysis", label: "Failure Analysis", icon: SearchCode },
  { to: "/experiments", label: "Experiments", icon: FlaskConical },
];

export default function Sidebar() {
  const { history, clearHistory } = useHistory();
  const navigate = useNavigate();

  function handleNewChat() {
    navigate("/");
    window.dispatchEvent(new CustomEvent("new-chat"));
  }

  function handleHistoryClick(question: string) {
    navigate(`/?q=${encodeURIComponent(question)}`);
  }

  return (
    <aside className="flex h-full w-60 shrink-0 flex-col border-r border-line bg-surface">
      {/* Logo */}
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-7 w-7 items-center justify-center rounded bg-accent text-sm font-semibold text-white">
          T
        </div>
        <span className="text-sm font-semibold tracking-tight">Test Insight</span>
      </div>

      {/* New Chat Button */}
      <div className="px-3 pb-3">
        <button
          onClick={handleNewChat}
          className="flex w-full items-center gap-2 rounded border border-line px-3 py-2 text-sm text-slate transition-colors hover:bg-accent-soft/60 hover:text-ink"
        >
          <Plus size={15} />
          New Chat
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-1 px-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-accent-soft font-medium text-accent"
                  : "text-slate hover:bg-accent-soft/60 hover:text-ink"
              }`
            }
          >
            <Icon size={16} strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Recent History */}
      {history.length > 0 && (
        <div className="mt-4 flex flex-1 flex-col overflow-hidden px-3">
          <div className="mb-1 flex items-center justify-between px-2">
            <span className="flex items-center gap-1.5 text-xs font-medium text-slate">
              <Clock size={12} />
              Recent
            </span>
            <button
              onClick={clearHistory}
              className="text-slate hover:text-red-400 transition-colors"
              title="Clear history"
            >
              <Trash2 size={12} />
            </button>
          </div>
          <div className="flex flex-col gap-0.5 overflow-y-auto">
            {history.map((item) => (
              <button
                key={item.id}
                onClick={() => handleHistoryClick(item.question)}
                className="w-full truncate rounded px-3 py-1.5 text-left text-xs text-slate transition-colors hover:bg-accent-soft/60 hover:text-ink"
                title={item.question}
              >
                {item.question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="border-t border-line px-5 py-4 text-xs text-slate">
        Worklet 26SE08 · Frontend v0.1
      </div>
    </aside>
  );
}
