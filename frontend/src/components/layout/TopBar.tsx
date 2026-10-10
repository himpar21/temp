import { useEffect, useState } from "react";
import { LogOut, Moon, Sun } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { useRole } from "../../context/RoleContext";

export default function TopBar({ title }: { title: string }) {
  const { role } = useRole();
  const [dark, setDark] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-line bg-surface px-6">
      <h1 className="text-sm font-medium text-ink">{title}</h1>
      <div className="flex items-center gap-3">
        <div className="hidden text-right sm:block">
          <p className="text-xs font-medium text-ink">{user?.full_name}</p>
          <p className="text-xs text-slate">{user?.email}</p>
        </div>
        <span
          aria-label="Current role"
          className="rounded border border-line bg-surface px-2.5 py-1.5 text-xs text-ink"
        >
          {role}
        </span>
        <button
          onClick={() => setDark((d) => !d)}
          aria-label="Toggle dark mode"
          className="flex h-7 w-7 items-center justify-center rounded border border-line text-slate hover:text-ink"
        >
          {dark ? <Sun size={14} /> : <Moon size={14} />}
        </button>
        <button
          onClick={async () => {
            setLoggingOut(true);
            await logout();
            navigate("/login", { replace: true });
          }}
          disabled={loggingOut}
          aria-label="Log out"
          className="flex items-center gap-1.5 rounded border border-line px-2.5 py-1.5 text-xs text-slate hover:text-fail disabled:opacity-50"
        >
          <LogOut size={14} />
          <span className="hidden sm:inline">Log out</span>
        </button>
      </div>
    </header>
  );
}
