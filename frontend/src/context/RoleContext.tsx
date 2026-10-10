import { createContext, useContext } from "react";
import { useAuth } from "../auth/AuthContext";

export const ROLES = ["Admin", "Test Lead", "Tester"] as const;
export type Role = (typeof ROLES)[number];

interface RoleContextType {
  role: Role;
}

const RoleContext = createContext<RoleContextType>({
  role: "Test Lead",
});

export function RoleProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const role: Role = user?.role ?? "Tester";
  return (
    <RoleContext.Provider value={{ role }}>
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  return useContext(RoleContext);
}
