import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../lib/api";
import { canIngest } from "../lib/rbac";
import { useAuth } from "../providers/AuthProvider";

type Doc = {
  id: string;
  title: string;
  sensitivity: string;
  ingest_status: string;
  allowed_roles: string[];
};

export function KnowledgePage() {
  const { token, roles } = useAuth();
  const [items, setItems] = useState<Doc[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!token) return;
    const data = await apiFetch<{ items: Doc[] }>("/api/knowledge/documents", token);
    setItems(data.items);
  }, [token]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function handleIngest() {
    if (!token) return;
    const result = await apiFetch<{ task_id: string }>("/api/knowledge/ingest", token, {
      method: "POST",
      body: JSON.stringify({ force: true }),
    });
    setMessage(`Ingest queued: ${result.task_id}`);
    window.setTimeout(() => {
      void refresh();
    }, 2000);
  }

  return (
    <div data-testid="knowledge-page">
      <h1>Knowledge</h1>
      <p style={{ color: "var(--ink-muted)" }}>
        Celery ingests docs into pgvector with role metadata for permission-aware RAG.
      </p>
      {canIngest(roles) ? (
        <button type="button" className="btn" onClick={() => void handleIngest()}>
          Run ingest
        </button>
      ) : null}
      {message ? <p className="mono">{message}</p> : null}
      <div className="panel" style={{ marginTop: "1rem" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Sensitivity</th>
              <th>Roles</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.title}</td>
                <td>{item.sensitivity}</td>
                <td className="mono">{item.allowed_roles?.join(", ")}</td>
                <td>{item.ingest_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
