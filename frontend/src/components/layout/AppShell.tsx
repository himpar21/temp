import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import { RoleProvider } from "../../context/RoleContext";
import { HistoryProvider } from "../../context/HistoryContext";

const TITLES: Record<string, string> = {
  "/": "Query Console",
  "/data": "Data Browser",
  "/upload": "Upload Data",
  "/failure-analysis": "Failure Analysis",
  "/experiments": "Experiments",
};

export default function AppShell() {
  const location = useLocation();
  const title = TITLES[location.pathname] ?? "Test Insight";

  return (
    <RoleProvider>
      <HistoryProvider>
        <div className="flex h-screen w-full overflow-hidden bg-paper text-ink">
          <Sidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <TopBar title={title} />
            <main className="flex-1 overflow-y-auto px-6 py-6">
              <Outlet />
            </main>
          </div>
        </div>
      </HistoryProvider>
    </RoleProvider>
  );
}
