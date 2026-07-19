import { useEffect, useState } from "react";

import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type ToolRow = {
  tool_name: string;
  user_sub: string;
  success: boolean;
  latency_ms: number;
};

export function AuditPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<ToolRow[]>([]);

  useEffect(() => {
    if (!token) return;
    void apiFetch<{ items: ToolRow[] }>("/api/audit/tools", token).then((data) =>
      setItems(data.items),
    );
  }, [token]);

  return (
    <div data-testid="audit-page">
      <h1>Audit</h1>
      <div className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Tool</th>
              <th>User</th>
              <th>OK</th>
              <th>Latency</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={`${item.tool_name}-${index}`}>
                <td className="mono">{item.tool_name}</td>
                <td>{item.user_sub}</td>
                <td>{item.success ? "yes" : "no"}</td>
                <td>{item.latency_ms} ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
