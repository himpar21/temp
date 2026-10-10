import { Routes, Route } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import QueryConsolePage from "./pages/QueryConsolePage";
import DataBrowserPage from "./pages/DataBrowserPage";
import UploadPage from "./pages/UploadPage";
import FailureAnalysisPage from "./pages/FailureAnalysisPage";
import ExperimentsPage from "./pages/ExperimentsPage";
import AuthPage from "./pages/AuthPage";
import ProtectedRoute from "./auth/ProtectedRoute";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<QueryConsolePage />} />
          <Route path="/data" element={<DataBrowserPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/failure-analysis" element={<FailureAnalysisPage />} />
          <Route path="/experiments" element={<ExperimentsPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
