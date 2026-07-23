import { Ticket } from "lucide-react";
import { useEffect, useState } from "react";

import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type CaseItem = {
  issue_key: string;
  title: string;
  status: string;
  priority: string;
  customer_name: string;
};

export function CasesPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<CaseItem[]>([]);

  useEffect(() => {
    if (!token) return;
    void apiFetch<{ items: CaseItem[] }>("/api/desk/cases", token).then((data) =>
      setItems(data.items),
    );
  }, [token]);

  return (
    <div data-testid="issues-page" className="p-6 lg:p-8">
      <PageHeader
        icon={Ticket}
        title="Issues"
        description="Open and recent support cases across the account portfolio."
      />
      <div className="card overflow-hidden">
        <table className="table">
          <thead>
            <tr>
              <th>Key</th>
              <th>Customer</th>
              <th>Title</th>
              <th>Priority</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.issue_key}>
                <td className="mono">{item.issue_key}</td>
                <td>{item.customer_name}</td>
                <td>{item.title}</td>
                <td>{item.priority}</td>
                <td>{item.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
