import { Navigate, Route, Routes } from "react-router-dom";

import { DeskShell } from "./components/layout/DeskShell";
import { AccountProfilePage } from "./pages/AccountProfilePage";
import { AccountSecurityPage } from "./pages/AccountSecurityPage";
import { AccountsPage } from "./pages/AccountsPage";
import { AdminPage } from "./pages/AdminPage";
import { ApprovalsPage } from "./pages/ApprovalsPage";
import { AssistantPage } from "./pages/AssistantPage";
import { AuditPage } from "./pages/AuditPage";
import { CasesPage } from "./pages/CasesPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EvaluationsPage } from "./pages/EvaluationsPage";
import { GovernancePage } from "./pages/GovernancePage";
import { FaqPage, PlatformGuidePage } from "./pages/HelpPages";
import { KnowledgePage } from "./pages/KnowledgePage";
import { LoginPage } from "./pages/LoginPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TasksPage } from "./pages/TasksPage";
import {
  AiInformationNoticePage,
  PrivacyPolicyPage,
  SecurityDataProtectionPage,
} from "./pages/TrustPages";
import { useAuth } from "./providers/AuthProvider";

export function App() {
  const { ready, authenticated } = useAuth();

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-relay-mesh">
        <div className="card px-8 py-6 text-center shadow-soft">
          <p className="font-display text-lg font-semibold text-ink-primary">Relay</p>
          <p className="mt-1 text-sm text-ink-secondary">Starting Command Desk…</p>
        </div>
      </div>
    );
  }

  if (!authenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<LoginPage />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<Navigate to="/assistant" replace />} />
      <Route element={<DeskShell />}>
        <Route path="/" element={<Navigate to="/assistant" replace />} />
        <Route path="/assistant" element={<AssistantPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/desk" element={<Navigate to="/dashboard" replace />} />
        <Route path="/customers" element={<AccountsPage />} />
        <Route path="/accounts" element={<Navigate to="/customers" replace />} />
        <Route path="/issues" element={<CasesPage />} />
        <Route path="/cases" element={<Navigate to="/issues" replace />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/approvals" element={<ApprovalsPage />} />
        <Route path="/knowledge" element={<KnowledgePage />} />
        <Route path="/evaluations" element={<EvaluationsPage />} />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="/audit-logs" element={<Navigate to="/audit" replace />} />
        <Route path="/governance" element={<GovernancePage />} />
        <Route path="/ai-governance" element={<Navigate to="/governance" replace />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/account/profile" element={<AccountProfilePage />} />
        <Route path="/account/security" element={<AccountSecurityPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/trust/privacy" element={<PrivacyPolicyPage />} />
        <Route path="/trust/ai-information" element={<AiInformationNoticePage />} />
        <Route path="/trust/security" element={<SecurityDataProtectionPage />} />
        <Route path="/help/guide" element={<PlatformGuidePage />} />
        <Route path="/help/faq" element={<FaqPage />} />
        <Route path="*" element={<Navigate to="/assistant" replace />} />
      </Route>
    </Routes>
  );
}
