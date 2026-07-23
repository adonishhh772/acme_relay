import { Building2, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type AccountRisk = {
  external_id: string;
  name: string;
  industry: string | null;
  tier: string;
  region: string | null;
  account_owner: string | null;
  support_manager: string | null;
  account_manager: string | null;
  contract_value_gbp: number | null;
  renewal_date: string | null;
  open_issues: number;
  critical_issues: number;
  sla_at_risk: number;
  risk_score: number;
  risk_status: string;
  recommended_action: string;
};

type Account360 = {
  account: AccountRisk;
  open_issues: Array<{
    issue_key: string;
    title: string;
    status: string;
    priority: string;
    assigned_to: string | null;
  }>;
  next_actions: Array<{
    action_text: string;
    owner: string | null;
    status: string;
    issue_key: string;
  }>;
};

function formatGbp(value: number | null): string {
  if (value == null) return "—";
  if (value >= 1_000_000) return `£${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `£${Math.round(value / 1_000)}K`;
  return `£${value}`;
}

function riskTone(status: string): string {
  if (status === "red") return "text-relay-danger";
  if (status === "amber") return "text-relay-warn";
  return "text-relay-mint";
}

export function AccountsPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<AccountRisk[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Account360 | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  const loadAccounts = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const data = await apiFetch<{ items: AccountRisk[] }>("/api/desk/accounts", token);
      setItems(data.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load accounts");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void loadAccounts();
  }, [loadAccounts]);

  const openAccount = useCallback(
    async (externalId: string) => {
      if (!token) return;
      setSelectedId(externalId);
      setIsDetailLoading(true);
      try {
        const data = await apiFetch<Account360>(
          `/api/desk/accounts/${encodeURIComponent(externalId)}`,
          token,
        );
        setDetail(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load account");
        setDetail(null);
      } finally {
        setIsDetailLoading(false);
      }
    },
    [token],
  );

  function handleSelectAccount(externalId: string) {
    void openAccount(externalId);
  }

  function handleCloseDetail() {
    setSelectedId(null);
    setDetail(null);
  }

  return (
    <div data-testid="customers-page" className="p-6 lg:p-8">
      <PageHeader
        icon={Building2}
        title="Account portfolio"
        description="Account management health — contract, renewal, risk, and open work."
      />

      {error ? <p className="error-text mb-4">{error}</p> : null}
      {isLoading ? <p className="text-sm text-ink-muted">Loading accounts…</p> : null}

      <div className="card overflow-hidden">
        <table className="table">
          <thead>
            <tr>
              <th>Account</th>
              <th>Tier</th>
              <th>Owner</th>
              <th>Contract</th>
              <th>Renewal</th>
              <th>Open</th>
              <th>Critical</th>
              <th>Risk</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.external_id}>
                <td>
                  <button
                    type="button"
                    className="text-left font-medium text-relay-cyan hover:underline"
                    onClick={() => handleSelectAccount(item.external_id)}
                    data-testid={`account-${item.external_id}`}
                  >
                    {item.name}
                  </button>
                  <p className="mono text-xs text-ink-muted">{item.external_id}</p>
                </td>
                <td>
                  <span className="pill">{item.tier}</span>
                </td>
                <td>{item.account_owner ?? "—"}</td>
                <td>{formatGbp(item.contract_value_gbp)}</td>
                <td className="mono text-xs">{item.renewal_date ?? "—"}</td>
                <td>{item.open_issues}</td>
                <td>{item.critical_issues}</td>
                <td>
                  <span className={`font-semibold ${riskTone(item.risk_status)}`}>
                    {item.risk_status} ({item.risk_score})
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedId ? (
        <div
          className="fixed inset-0 z-40 flex justify-end bg-slate-900/30"
          data-testid="account-360-drawer"
        >
          <button
            type="button"
            className="flex-1 cursor-default"
            aria-label="Close account drawer"
            onClick={handleCloseDetail}
          />
          <aside className="h-full w-full max-w-lg overflow-y-auto border-l border-surface-border bg-white p-6 shadow-soft">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <p className="section-label">Account 360</p>
                <h2 className="font-display text-xl font-semibold">
                  {detail?.account.name ?? selectedId}
                </h2>
              </div>
              <button type="button" className="btn-ghost" onClick={handleCloseDetail}>
                <X className="h-4 w-4" />
              </button>
            </div>

            {isDetailLoading ? (
              <p className="text-sm text-ink-muted">Loading account…</p>
            ) : null}

            {detail ? (
              <div className="space-y-5">
                <div className="grid grid-cols-2 gap-3">
                  <div className="card p-3">
                    <p className="section-label">Risk</p>
                    <p className={`font-semibold ${riskTone(detail.account.risk_status)}`}>
                      {detail.account.risk_status} · {detail.account.risk_score}
                    </p>
                  </div>
                  <div className="card p-3">
                    <p className="section-label">Contract</p>
                    <p className="font-semibold">
                      {formatGbp(detail.account.contract_value_gbp)}
                    </p>
                  </div>
                  <div className="card p-3">
                    <p className="section-label">Renewal</p>
                    <p className="font-semibold mono text-sm">
                      {detail.account.renewal_date ?? "—"}
                    </p>
                  </div>
                  <div className="card p-3">
                    <p className="section-label">Support manager</p>
                    <p className="font-semibold text-sm">
                      {detail.account.support_manager ?? "—"}
                    </p>
                  </div>
                </div>

                <div>
                  <p className="section-label mb-2">Recommended action</p>
                  <p className="text-sm text-ink-secondary">
                    {detail.account.recommended_action}
                  </p>
                </div>

                <div>
                  <p className="section-label mb-2">Open issues</p>
                  <ul className="space-y-2">
                    {detail.open_issues.map((issue) => (
                      <li key={issue.issue_key} className="card p-3 text-sm">
                        <p className="font-medium">
                          {issue.issue_key} · {issue.title}
                        </p>
                        <p className="text-ink-muted">
                          {issue.priority} · {issue.status}
                          {issue.assigned_to ? ` · ${issue.assigned_to}` : ""}
                        </p>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <p className="section-label mb-2">Next actions</p>
                  {detail.next_actions.length === 0 ? (
                    <p className="text-sm text-ink-muted">No pending actions.</p>
                  ) : (
                    <ul className="space-y-2">
                      {detail.next_actions.map((action) => (
                        <li
                          key={`${action.issue_key}-${action.action_text}`}
                          className="card p-3 text-sm"
                        >
                          <p className="font-medium">{action.action_text}</p>
                          <p className="text-ink-muted">
                            {action.issue_key} · {action.status}
                            {action.owner ? ` · ${action.owner}` : ""}
                          </p>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ) : null}
          </aside>
        </div>
      ) : null}
    </div>
  );
}
