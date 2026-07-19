import { useEffect, useState } from "react";

import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type Account = {
  external_id: string;
  name: string;
  industry: string;
  tier: string;
  account_owner: string;
};

export function AccountsPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<Account[]>([]);

  useEffect(() => {
    if (!token) return;
    void apiFetch<{ items: Account[] }>("/api/desk/accounts", token).then((data) =>
      setItems(data.items),
    );
  }, [token]);

  return (
    <div data-testid="customers-page">
      <h1>Customers</h1>
      <div className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>ID</th>
              <th>Tier</th>
              <th>Owner</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.external_id}>
                <td>{item.name}</td>
                <td className="mono">{item.external_id}</td>
                <td>
                  <span className="pill">{item.tier}</span>
                </td>
                <td>{item.account_owner}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
