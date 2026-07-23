import { LayoutGrid } from "lucide-react";
import { useEffect, useState } from "react";

import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type Summary = {
  open_cases: number;
  critical_cases: number;
  pending_actions: number;
  active_accounts: number;
};

export function DeskPage() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<Summary | null>(null);

  useEffect(() => {
    if (!token) return;
    void apiFetch<Summary>("/api/desk/summary", token).then(setSummary);
  }, [token]);

  return (
    <div data-testid="desk-page" className="p-6 lg:p-8">
      <PageHeader
        icon={LayoutGrid}
        title="Desk"
        description="Lightweight snapshot of open cases and pending actions for your role."
      />
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="card p-4">
          <p className="section-label">Open cases</p>
          <strong className="mt-1 block font-display text-2xl">
            {summary?.open_cases ?? "—"}
          </strong>
        </div>
        <div className="card p-4">
          <p className="section-label">Critical</p>
          <strong className="mt-1 block font-display text-2xl">
            {summary?.critical_cases ?? "—"}
          </strong>
        </div>
        <div className="card p-4">
          <p className="section-label">Pending actions</p>
          <strong className="mt-1 block font-display text-2xl">
            {summary?.pending_actions ?? "—"}
          </strong>
        </div>
      </div>
    </div>
  );
}
