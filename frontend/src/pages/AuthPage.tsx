import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { FlaskConical } from "lucide-react";
import { useAuth } from "../auth/AuthContext";

export default function AuthPage() {
  const { user, login, signup } = useAuth();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"Admin" | "Test Lead" | "Tester" | "">("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (mode === "signup") await signup(fullName, email, role as "Admin" | "Test Lead" | "Tester", password, confirmPassword);
      else await login(email, password);
      const destination = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? "/";
      navigate(destination, { replace: true });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Authentication failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-paper px-4 py-10 text-ink">
      <section className="w-full max-w-md rounded-xl border border-line bg-surface p-7 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-white">
            <FlaskConical size={20} />
          </span>
          <div>
            <h1 className="text-xl font-semibold">Test Insight</h1>
            <p className="text-sm text-slate">Secure AI test execution insights</p>
          </div>
        </div>

        <div className="mb-6 grid grid-cols-2 rounded-lg bg-paper p-1 text-sm">
          {(["login", "signup"] as const).map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => { setMode(item); setError(null); setPassword(""); setConfirmPassword(""); }}
              className={`rounded-md px-3 py-2 font-medium capitalize ${
                mode === item ? "bg-surface text-accent shadow-sm" : "text-slate"
              }`}
            >
              {item === "login" ? "Log in" : "Sign up"}
            </button>
          ))}
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          {mode === "signup" && (
            <label className="block text-sm">
              <span className="mb-1.5 block font-medium">Full name</span>
              <input
                required minLength={2} maxLength={120} autoComplete="name"
                value={fullName} onChange={(event) => setFullName(event.target.value)}
                className="w-full rounded-lg border border-line bg-paper px-3 py-2.5 outline-none focus:ring-2 focus:ring-accent"
              />
            </label>
          )}
          <label className="block text-sm">
            <span className="mb-1.5 block font-medium">Email</span>
            <input
              required type="email" autoComplete="email" value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-lg border border-line bg-paper px-3 py-2.5 outline-none focus:ring-2 focus:ring-accent"
            />
          </label>
          {mode === "signup" && (
            <label className="block text-sm">
              <span className="mb-1.5 block font-medium">Role</span>
              <select
                required value={role} onChange={(event) => setRole(event.target.value as typeof role)}
                className="w-full rounded-lg border border-line bg-paper px-3 py-2.5 outline-none focus:ring-2 focus:ring-accent"
              >
                <option value="" disabled>Select a role</option>
                <option value="Admin">Admin</option>
                <option value="Test Lead">Test Lead</option>
                <option value="Tester">Tester</option>
              </select>
            </label>
          )}
          <label className="block text-sm">
            <span className="mb-1.5 block font-medium">Password</span>
            <input
              required type="password" minLength={mode === "signup" ? 8 : 1} maxLength={128}
              autoComplete={mode === "signup" ? "new-password" : "current-password"}
              pattern={mode === "signup" ? "(?=.*[A-Z])(?=.*\\d)(?=.*[^A-Za-z0-9]).{8,}" : undefined}
              title={mode === "signup" ? "Use at least 8 characters with an uppercase letter, number, and special character." : undefined}
              value={password} onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-lg border border-line bg-paper px-3 py-2.5 outline-none focus:ring-2 focus:ring-accent"
            />
            {mode === "signup" && (
              <span className="mt-1 block text-xs text-slate">
                At least 8 characters with an uppercase letter, number, and special character.
              </span>
            )}
          </label>
          {mode === "signup" && (
            <label className="block text-sm">
              <span className="mb-1.5 block font-medium">Confirm password</span>
              <input
                required type="password" minLength={8} maxLength={128} autoComplete="new-password"
                value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)}
                pattern="(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}"
                title="Use at least 8 characters with an uppercase letter, number, and special character."
                className="w-full rounded-lg border border-line bg-paper px-3 py-2.5 outline-none focus:ring-2 focus:ring-accent"
              />
              {confirmPassword && password !== confirmPassword && (
                <span className="mt-1 block text-xs text-fail">Passwords do not match.</span>
              )}
            </label>
          )}

          {error && <p role="alert" className="rounded-lg bg-fail/10 px-3 py-2 text-sm text-fail">{error}</p>}

          <button
            type="submit" disabled={submitting || (mode === "signup" && password !== confirmPassword)}
            className="w-full rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {submitting ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
          </button>
        </form>
      </section>
    </main>
  );
}
