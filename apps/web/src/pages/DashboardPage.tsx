import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiFetch } from "../lib/api";
import { canViewOrgWideInsights } from "../lib/rbac";
import { useAuth } from "../providers/AuthProvider";

type Summary = {
  open_cases: number;
  critical_cases: number;
  pending_actions: number;
  active_accounts: number;
  sla_breach_risk: number;
  open_tasks: number;
  groundedness_pass_rate_7d: number | null;
  role_scope: string[];
};

export function DashboardPage() {
  const { token, roles } = useAuth();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    void apiFetch<Summary>("/api/desk/summary", token)
      .then((data) => {
        setSummary(data);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, [token]);

  return (
    <div data-testid="dashboard-page">
      <h1>Dashboard</h1>
      <p className="page-lead">
        Command Centre KPIs for your role
        {summary?.role_scope?.length ? ` (${summary.role_scope.join(", ")})` : ""}.
      </p>
      {error ? <p className="error-text">{error}</p> : null}
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
        <div className="stat">
          Active accounts
          <strong>{summary?.active_accounts ?? "—"}</strong>
        </div>
        <div className="stat">
          SLA risk (4h)
          <strong>{summary?.sla_breach_risk ?? "—"}</strong>
        </div>
        <div className="stat">
          Open tasks
          <strong>{summary?.open_tasks ?? "—"}</strong>
        </div>
        {canViewOrgWideInsights(roles) ? (
          <div className="stat">
            Groundedness (7d)
            <strong>
              {summary?.groundedness_pass_rate_7d != null
                ? `${summary.groundedness_pass_rate_7d}%`
                : "—"}
            </strong>
          </div>
        ) : null}
      </div>
      <div className="card-row">
        <Link className="btn secondary" to="/customers">
          Customers
        </Link>
        <Link className="btn secondary" to="/issues">
          Issues
        </Link>
        <Link className="btn secondary" to="/tasks">
          Tasks
        </Link>
        <Link className="btn secondary" to="/approvals">
          Approvals
        </Link>
      </div>
    </div>
  );
}
