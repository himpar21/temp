import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: "Admin" | "Test Lead" | "Tester";
  created_at: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (fullName: string, email: string, role: AuthUser["role"], password: string, confirmPassword: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function errorMessage(response: Response, fallback: string) {
  const body = await response.json().catch(() => null);
  if (typeof body?.detail === "string") return body.detail;
  if (Array.isArray(body?.detail)) return body.detail[0]?.msg ?? fallback;
  return fallback;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/auth/session", { credentials: "include" })
      .then(async (response) => {
        if (response.ok) setUser((await response.json()) as AuthUser);
        else setUser(null);
      })
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  async function authenticate(path: "login" | "signup", body: Record<string, string>) {
    const response = await fetch(`/api/v1/auth/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(await errorMessage(response, "Authentication failed"));
    const result = (await response.json()) as { user: AuthUser };
    setUser(result.user);
  }

  async function logout() {
    try {
      await fetch("/api/v1/auth/logout", { method: "POST", credentials: "include" });
    } finally {
      setUser(null);
    }
  }

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    login: (email, password) => authenticate("login", { email, password }),
    signup: (fullName, email, role, password, confirmPassword) => authenticate("signup", {
      full_name: fullName,
      email,
      role,
      password,
      confirm_password: confirmPassword,
    }),
    logout,
  }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
