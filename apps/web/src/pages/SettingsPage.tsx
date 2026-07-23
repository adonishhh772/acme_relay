import { Settings } from "lucide-react";
import { useEffect, useState } from "react";

import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import { canManageUsers } from "../lib/rbac";
import { useAuth } from "../providers/AuthProvider";

type PromptInfo = {
  active?: {
    name: string;
    version: number;
    labels?: string[];
    description?: string;
  };
};

type McpStatus = {
  agent_tools_enabled: boolean;
  agent_tools_loaded: boolean;
  agent_tool_count: number;
  agent_tools_error?: string | null;
  servers: Array<{
    name: string;
    url?: string;
    reachable: boolean;
    status_code?: number | null;
    error?: string | null;
  }>;
};

export function SettingsPage() {
  const { token, roles } = useAuth();
  const [prompt, setPrompt] = useState<PromptInfo | null>(null);
  const [mcp, setMcp] = useState<McpStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const admin = canManageUsers(roles);

  async function refresh() {
    if (!token) {
      return;
    }
    setIsLoading(true);
    try {
      const [promptResponse, mcpResponse] = await Promise.all([
        apiFetch<PromptInfo>("/api/governance/prompts", token).catch(() => null),
        apiFetch<McpStatus>("/api/mcp/status", token),
      ]);
      setPrompt(promptResponse);
      setMcp(mcpResponse);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, [token]);

  return (
    <div data-testid="settings-page" className="p-6 lg:p-8">
      <PageHeader
        icon={Settings}
        title="Settings"
        description="Runtime health for MCP tools, prompt version, and observability links you actually use during a demo."
        actions={
          <button
            type="button"
            className="btn-secondary"
            onClick={() => void refresh()}
            disabled={isLoading}
          >
            Refresh status
          </button>
        }
      />

      {error ? <p className="error-text">{error}</p> : null}

      <div className="space-y-4">
        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">MCP agent tools</h2>
          <p className="mt-1 text-sm text-ink-secondary">
            The assistant loads these at API startup. If count is 0, chat still works with native
            tools only.
          </p>
          <dl className="mt-4 grid gap-3 sm:grid-cols-3">
            <div>
              <dt className="section-label">Enabled</dt>
              <dd className="mt-1 font-semibold">
                {mcp ? String(mcp.agent_tools_enabled) : "—"}
              </dd>
            </div>
            <div>
              <dt className="section-label">Loaded</dt>
              <dd className="mt-1 font-semibold">
                {mcp ? String(mcp.agent_tools_loaded) : "—"}
              </dd>
            </div>
            <div>
              <dt className="section-label">Tool count</dt>
              <dd className="mt-1 font-semibold">{mcp?.agent_tool_count ?? "—"}</dd>
            </div>
          </dl>
          {mcp?.agent_tools_error ? (
            <p className="error-text mt-3">{mcp.agent_tools_error}</p>
          ) : null}
          <ul className="mt-4 space-y-2">
            {(mcp?.servers ?? []).map((server) => (
              <li
                key={server.name}
                className="flex items-center justify-between rounded-xl bg-surface-muted px-3 py-2 text-sm"
              >
                <span className="font-medium capitalize">{server.name}</span>
                <span className={server.reachable ? "text-teal-700" : "text-relay-danger"}>
                  {server.reachable ? "reachable" : "unreachable"}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">System prompt</h2>
          {prompt?.active ? (
            <>
              <p className="mt-2 font-mono text-sm">
                {prompt.active.name} v{prompt.active.version}
                {prompt.active.labels?.includes("production") ? " · production" : ""}
              </p>
              {prompt.active.description ? (
                <p className="mt-2 text-sm text-ink-secondary">{prompt.active.description}</p>
              ) : null}
            </>
          ) : (
            <p className="mt-2 text-sm text-ink-muted">
              {admin
                ? "Prompt metadata unavailable."
                : "Prompt details require an elevated role (admin/approver)."}
            </p>
          )}
          {admin ? (
            <p className="mt-3 text-sm text-ink-secondary">
              Manage promotion story under <strong>AI Governance → Prompt</strong>.
            </p>
          ) : null}
        </section>

        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">Observability</h2>
          <p className="mt-1 text-sm text-ink-secondary">
            Open these while the Compose stack is up. Traces appear after you send a chat.
          </p>
          <ul className="mt-4 space-y-2 text-sm">
            <li>
              <a className="text-relay-cyan underline" href="http://localhost:3001" target="_blank" rel="noreferrer">
                Langfuse
              </a>{" "}
              — agent runs, tool spans
            </li>
            <li>
              <a className="text-relay-cyan underline" href="http://localhost:3002" target="_blank" rel="noreferrer">
                Grafana
              </a>{" "}
              — metrics (admin / admin)
            </li>
            <li>
              <a className="text-relay-cyan underline" href="http://localhost:8001" target="_blank" rel="noreferrer">
                GlitchTip
              </a>{" "}
              — exceptions
            </li>
            <li>
              <a className="text-relay-cyan underline" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
                API docs
              </a>{" "}
              — OpenAPI
            </li>
          </ul>
        </section>

        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">Identity</h2>
          <p className="mt-1 text-sm text-ink-secondary">
            Profile and MFA are managed in Relay (Profile / Security). Keycloak remains the
            identity provider that issues JWTs.
          </p>
          <a
            className="btn-secondary mt-4 inline-flex"
            href="http://localhost:8080"
            target="_blank"
            rel="noreferrer"
          >
            Open Keycloak admin
          </a>
        </section>
      </div>
    </div>
  );
}
