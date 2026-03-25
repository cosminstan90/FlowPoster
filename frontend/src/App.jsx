import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import AppLayout from "./layouts/AppLayout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ProjectPage from "./pages/ProjectPage";
import CampaignPage from "./pages/CampaignPage";
import PageEditor from "./pages/PageEditor";
import CostReport from "./pages/CostReport";
import Templates from "./pages/Templates";
import TemplateEditPage from "./pages/TemplateEditPage";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="/projects/new" element={<Navigate to="/" replace />} />
            <Route path="/projects/:id" element={<ProjectPage />} />
            <Route path="/campaigns/:id" element={<CampaignPage />} />
            <Route path="/pages/:id" element={<PageEditor />} />
            <Route path="/costs" element={<CostReport />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/templates/:id" element={<TemplateEditPage />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
