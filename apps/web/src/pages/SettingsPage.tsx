import { useEffect, useState } from "react";

import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type PromptInfo = {
  active?: {
    name: string;
    version: number;
    labels?: string[];
  };
};

type McpStatus = {
  agent_tools_enabled: boolean;
  agent_tools_loaded: boolean;
  agent_tool_count: number;
  servers: Array<{ name: string; reachable: boolean }>;
};

export function SettingsPage() {
  const { token } = useAuth();
  const [prompt, setPrompt] = useState<PromptInfo | null>(null);
  const [mcp, setMcp] = useState<McpStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    void Promise.all([
      apiFetch<PromptInfo>("/api/governance/prompts", token).catch(() => null),
      apiFetch<McpStatus>("/api/mcp/status", token).catch(() => null),
    ])
      .then(([promptResponse, mcpResponse]) => {
        setPrompt(promptResponse);
        setMcp(mcpResponse);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, [token]);

  return (
    <div data-testid="settings-page">
      <h1>Settings</h1>
      <p className="page-lead">Prompt version, MCP agent tools, and observability pointers.</p>
      {error ? <p className="error-text">{error}</p> : null}
      <section className="panel">
        <h2>System prompt</h2>
        <p>
          {prompt?.active
            ? `${prompt.active.name} v${prompt.active.version}${
                prompt.active.labels?.includes("production") ? " (production)" : ""
              }`
            : "Unavailable for this role"}
        </p>
      </section>
      <section className="panel">
        <h2>MCP agent tools</h2>
        <p>
          Enabled: {mcp ? String(mcp.agent_tools_enabled) : "—"} · Loaded:{" "}
          {mcp ? String(mcp.agent_tools_loaded) : "—"} · Count: {mcp?.agent_tool_count ?? "—"}
        </p>
        <ul>
          {(mcp?.servers ?? []).map((server) => (
            <li key={server.name}>
              {server.name}: {server.reachable ? "reachable" : "unreachable"}
            </li>
          ))}
        </ul>
      </section>
      <section className="panel">
        <h2>Observability</h2>
        <ul>
          <li>Langfuse: http://localhost:3001</li>
          <li>Grafana: http://localhost:3002</li>
          <li>GlitchTip: http://localhost:8001</li>
        </ul>
      </section>
    </div>
  );
}
