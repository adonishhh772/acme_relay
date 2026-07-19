import { useEffect, useState } from "react";

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
    <div data-testid="desk-page">
      <h1>Desk</h1>
      <div className="grid-3">
        <div className="stat">
          Open cases
          <strong>{summary?.open_cases ?? "—"}</strong>
        </div>
        <div className="stat">
          Critical
          <strong>{summary?.critical_cases ?? "—"}</strong>
        </div>
        <div className="stat">
          Pending actions
          <strong>{summary?.pending_actions ?? "—"}</strong>
        </div>
      </div>
    </div>
  );
}
