import { CheckSquare } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type Approval = {
  approval_id: string;
  issue_key?: string;
  action_text?: string;
  owner?: string;
  tool?: string;
  source?: string;
  requested_by?: string;
};

export function ApprovalsPage() {
  const { token, roles } = useAuth();
  const [items, setItems] = useState<Approval[]>([]);
  const [error, setError] = useState<string | null>(null);
  const isAdmin = roles.includes("admin");

  const refresh = useCallback(async () => {
    if (!token) return;
    const data = await apiFetch<{ items: Approval[]; total?: number }>(
      "/api/approvals",
      token,
    );
    setItems(data.items);
  }, [token]);

  useEffect(() => {
    void refresh().catch((err: Error) => setError(err.message));
  }, [refresh]);

  async function decide(approval: Approval, approve: boolean) {
    if (!token) return;
    setError(null);
    try {
      await apiFetch("/api/approvals/decide", token, {
        method: "POST",
        body: JSON.stringify({
          approval_id: approval.approval_id,
          approve,
          issue_key: approval.issue_key,
          action_text: approval.action_text,
          owner: approval.owner,
        }),
      });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Decision failed");
    }
  }

  return (
    <div data-testid="approvals-page" className="p-6 lg:p-8">
      <PageHeader
        icon={CheckSquare}
        title="Approvals"
        description="Human-in-the-loop queue for seeded next actions and agent-staged mutations that need an admin decision."
      />
      {error ? <p className="mb-4 error-text">{error}</p> : null}
      <div className="card p-5">
        {items.length === 0 ? (
          <p className="text-sm text-ink-muted">No pending approvals.</p>
        ) : null}
        {items.map((item) => (
          <div
            key={item.approval_id}
            className="mb-4 border-b border-surface-border pb-4 last:mb-0 last:border-0 last:pb-0"
            data-testid={`approval-${item.approval_id}`}
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="mono text-xs text-ink-muted">{item.issue_key || "—"}</span>
              {item.tool ? (
                <span className="mono text-xs text-ink-muted">{item.tool}</span>
              ) : null}
              {item.source ? (
                <span className="text-xs uppercase tracking-wide text-ink-muted">
                  {item.source === "next_actions" ? "desk next action" : "agent staged"}
                </span>
              ) : null}
            </div>
            <p className="mt-1 text-sm text-ink-primary">{item.action_text}</p>
            {item.owner ? (
              <p className="mt-1 text-xs text-ink-secondary">Owner: {item.owner}</p>
            ) : null}
            {isAdmin ? (
              <div className="mt-3 flex gap-2">
                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => void decide(item, true)}
                >
                  Approve
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => void decide(item, false)}
                >
                  Reject
                </button>
              </div>
            ) : (
              <p className="mt-2 text-sm text-ink-muted">Waiting for admin approval.</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
