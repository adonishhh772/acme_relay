import { Scale } from "lucide-react";
import { useEffect, useState } from "react";

import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type Overview = {
  prompt: {
    name: string;
    version: number;
    labels: string[];
    description?: string;
  };
  metrics: {
    agent_runs_7d: number;
    groundedness_pass_rate_7d: number | null;
    pending_approvals: number;
    tool_calls_7d: number;
  };
  ai_system_register: Array<{
    name: string;
    owner: string;
    purpose: string;
    risk_level: string;
    status: string;
    controls: string[];
  }>;
  risk_register: Array<{
    id: string;
    title: string;
    level: string;
    mitigation: string;
    status: string;
  }>;
  recent_runs: Array<{
    request_id: string;
    query: string;
    tools_used: string[];
    latency_ms: number;
    groundedness_passed: boolean | null;
    groundedness_explanation: string | null;
    created_at: string;
  }>;
};

type Tab = "overview" | "systems" | "risks" | "prompt" | "runs";

export function GovernancePage() {
  const { token } = useAuth();
  const [data, setData] = useState<Overview | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    void apiFetch<Overview>("/api/governance/overview", token)
      .then((response) => {
        setData(response);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, [token]);

  return (
    <div data-testid="governance-page" className="p-6 lg:p-8">
      <PageHeader
        icon={Scale}
        title="AI Governance"
        description="Operating controls for Relay: system register, risk mitigations, prompt version, and live groundedness evidence from agent runs."
      />

      {error ? <p className="error-text">{error}</p> : null}

      <div className="mb-4 flex flex-wrap gap-2">
        {(
          [
            ["overview", "Overview"],
            ["systems", "AI systems"],
            ["risks", "Risk register"],
            ["prompt", "Prompt"],
            ["runs", "Recent runs"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={tab === id ? "btn-primary" : "btn-secondary"}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "overview" && data ? (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {[
              ["Agent runs (7d)", data.metrics.agent_runs_7d],
              [
                "Groundedness pass",
                data.metrics.groundedness_pass_rate_7d != null
                  ? `${data.metrics.groundedness_pass_rate_7d}%`
                  : "—",
              ],
              ["Pending approvals", data.metrics.pending_approvals],
              ["Tool calls (7d)", data.metrics.tool_calls_7d],
            ].map(([label, value]) => (
              <div key={String(label)} className="card p-4">
                <p className="section-label">{label}</p>
                <strong className="mt-1 block font-display text-2xl">{value}</strong>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {tab === "systems" && data ? (
        <div className="grid gap-4">
          {data.ai_system_register.map((system) => (
            <article key={system.name} className="card p-5">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="font-display text-lg font-semibold">{system.name}</h2>
                <span className="pill">{system.status}</span>
                <span className="text-xs font-semibold uppercase text-ink-muted">
                  risk: {system.risk_level}
                </span>
              </div>
              <p className="mt-2 text-sm text-ink-secondary">{system.purpose}</p>
              <p className="mt-1 text-xs text-ink-muted">Owner: {system.owner}</p>
              <ul className="mt-3 flex flex-wrap gap-2">
                {system.controls.map((control) => (
                  <li
                    key={control}
                    className="rounded-full bg-surface-muted px-2.5 py-1 text-xs text-ink-secondary"
                  >
                    {control}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      ) : null}

      {tab === "risks" && data ? (
        <div className="card overflow-hidden">
          <table className="data-table mt-0">
            <thead>
              <tr>
                <th>ID</th>
                <th>Risk</th>
                <th>Level</th>
                <th>Mitigation</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.risk_register.map((risk) => (
                <tr key={risk.id}>
                  <td className="mono">{risk.id}</td>
                  <td>{risk.title}</td>
                  <td>{risk.level}</td>
                  <td>{risk.mitigation}</td>
                  <td>
                    <span className="pill">{risk.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === "prompt" && data ? (
        <div className="card p-5">
          <p className="section-label">Active system prompt</p>
          <h2 className="mt-2 font-display text-xl font-semibold">
            {data.prompt.name} · v{data.prompt.version}
          </h2>
          <p className="mt-2 text-sm text-ink-secondary">{data.prompt.description}</p>
          <p className="mt-3 text-xs text-ink-muted">
            Labels: {data.prompt.labels.join(", ") || "none"}
          </p>
          <p className="mt-4 rounded-xl bg-surface-muted px-3 py-2 text-sm text-ink-secondary">
            Prompt YAML lives in <code>apps/api/prompts/</code>. Promote carefully — every chat run
            records prompt name/version on <code>agent_runs</code>.
          </p>
        </div>
      ) : null}

      {tab === "runs" && data ? (
        <div className="card overflow-hidden">
          <table className="data-table mt-0">
            <thead>
              <tr>
                <th>When</th>
                <th>Query</th>
                <th>Tools</th>
                <th>Grounded</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_runs.length === 0 ? (
                <tr>
                  <td colSpan={5}>No agent runs yet — ask the Assistant once.</td>
                </tr>
              ) : (
                data.recent_runs.map((run) => (
                  <tr key={run.request_id}>
                    <td className="mono text-xs">
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                    <td className="max-w-xs truncate">{run.query}</td>
                    <td className="mono text-xs">{(run.tools_used || []).join(", ") || "—"}</td>
                    <td>
                      {run.groundedness_passed == null
                        ? "—"
                        : run.groundedness_passed
                          ? "pass"
                          : "review"}
                    </td>
                    <td>{run.latency_ms} ms</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : null}

      {!data && !error ? <p className="text-sm text-ink-muted">Loading governance…</p> : null}
    </div>
  );
}
