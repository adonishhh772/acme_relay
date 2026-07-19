import { useEffect, useState } from "react";

import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type PromptInfo = {
  name: string;
  version: number;
  labels: string[];
  description?: string;
};

export function GovernancePage() {
  const { token } = useAuth();
  const [active, setActive] = useState<PromptInfo | null>(null);

  useEffect(() => {
    if (!token) return;
    void apiFetch<{ active: PromptInfo }>("/api/governance/prompts", token).then((data) =>
      setActive(data.active),
    );
  }, [token]);

  return (
    <div data-testid="governance-page">
      <h1>Governance</h1>
      <div className="panel">
        <h2>Active system prompt</h2>
        {active ? (
          <>
            <p className="mono">
              {active.name} · v{active.version}
            </p>
            <p>{active.description}</p>
            <p>Labels: {active.labels.join(", ")}</p>
          </>
        ) : (
          <p>Loading…</p>
        )}
      </div>
    </div>
  );
}
