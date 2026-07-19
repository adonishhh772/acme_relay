import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type Approval = {
  approval_id: string;
  issue_key?: string;
  action_text?: string;
  owner?: string;
  tool?: string;
};

export function ApprovalsPage() {
  const { token, roles } = useAuth();
  const [items, setItems] = useState<Approval[]>([]);
  const isAdmin = roles.includes("admin");

  const refresh = useCallback(async () => {
    if (!token) return;
    const data = await apiFetch<{ items: Approval[] }>("/api/approvals", token);
    setItems(data.items);
  }, [token]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function decide(approval: Approval, approve: boolean) {
    if (!token) return;
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
  }

  return (
    <div data-testid="approvals-page">
      <h1>Approvals</h1>
      <div className="panel">
        {items.length === 0 ? <p>No pending approvals.</p> : null}
        {items.map((item) => (
          <div key={item.approval_id} style={{ marginBottom: "1rem" }}>
            <div className="mono">{item.issue_key}</div>
            <p>{item.action_text}</p>
            {isAdmin ? (
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button type="button" className="btn" onClick={() => void decide(item, true)}>
                  Approve
                </button>
                <button
                  type="button"
                  className="btn secondary"
                  onClick={() => void decide(item, false)}
                >
                  Reject
                </button>
              </div>
            ) : (
              <p style={{ color: "var(--ink-muted)" }}>Waiting for admin approval.</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
