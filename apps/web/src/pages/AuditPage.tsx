import {
  ChevronDown,
  ChevronRight,
  ExternalLink,
  RefreshCw,
  ScrollText,
} from "lucide-react";
import { Fragment, useCallback, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import { canSeeAudit } from "../lib/rbac";
import { useAuth } from "../providers/AuthProvider";

type AuditTab = "tools" | "runs" | "approvals";

type AuditSummary = {
  window: string;
  tool_calls_7d: number;
  tool_failures_7d: number;
  mcp_calls_7d: number;
  native_calls_7d: number;
  avg_tool_latency_ms: number | null;
  agent_runs_7d: number;
  groundedness_pass_rate_7d: number | null;
  avg_run_latency_ms: number | null;
  approvals_pending_7d: number;
  approvals_approved_7d: number;
  approvals_rejected_7d: number;
};

type PageResponse<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
};

type ToolAuditRow = {
  id: string;
  request_id: string | null;
  user_sub: string | null;
  user_roles: string[] | null;
  tool_name: string;
  arguments: Record<string, unknown> | string | null;
  result_summary: string | null;
  latency_ms: number | null;
  success: boolean;
  source: string;
  created_at: string;
  langfuse_url?: string | null;
  glitchtip_url?: string | null;
};

type RunAuditRow = {
  id: string;
  request_id: string | null;
  user_sub: string | null;
  query: string;
  answer: string | null;
  tools_used: string[] | null;
  latency_ms: number | null;
  prompt_name: string | null;
  prompt_version: number | null;
  groundedness_passed: boolean | null;
  groundedness_explanation: string | null;
  created_at: string;
  langfuse_url?: string | null;
  glitchtip_url?: string | null;
};

type ApprovalAuditRow = {
  id: string;
  request_id: string;
  session_id: string;
  tool_name: string;
  arguments: Record<string, unknown> | string | null;
  created_by_sub: string;
  status: string;
  decided_by_sub: string | null;
  decided_at: string | null;
  created_at: string;
  langfuse_url?: string | null;
  glitchtip_url?: string | null;
};

function EventTraceLinks({
  langfuseUrl,
  glitchtipUrl,
}: {
  langfuseUrl?: string | null;
  glitchtipUrl?: string | null;
}) {
  const available = [
    langfuseUrl
      ? { href: langfuseUrl, label: "View in Langfuse", testId: "audit-link-langfuse" }
      : null,
    glitchtipUrl
      ? { href: glitchtipUrl, label: "Open GlitchTip", testId: "audit-link-glitchtip" }
      : null,
  ].filter((item): item is { href: string; label: string; testId: string } => item != null);

  if (available.length === 0) {
    return (
      <p className="text-xs text-ink-muted">
        Langfuse / GlitchTip not available for this event (missing request id or not
        configured).
      </p>
    );
  }

  return (
    <div className="flex flex-wrap gap-4" data-testid="audit-event-observability">
      {available.map((item) => (
        <a
          key={item.testId}
          href={item.href}
          target="_blank"
          rel="noreferrer"
          data-testid={item.testId}
          className="inline-flex items-center gap-1 text-sm font-medium text-relay-cyan hover:underline"
        >
          {item.label}
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      ))}
    </div>
  );
}

function formatWhen(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

function formatJson(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "string") {
    try {
      return JSON.stringify(JSON.parse(value), null, 2);
    } catch {
      return value;
    }
  }
  return JSON.stringify(value, null, 2);
}

function truncate(text: string | null | undefined, maxLength = 120): string {
  if (!text) return "—";
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}…`;
}

export function AuditPage() {
  const { token, roles } = useAuth();
  const [tab, setTab] = useState<AuditTab>("tools");
  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [tools, setTools] = useState<PageResponse<ToolAuditRow> | null>(null);
  const [runs, setRuns] = useState<PageResponse<RunAuditRow> | null>(null);
  const [approvals, setApprovals] = useState<PageResponse<ApprovalAuditRow> | null>(
    null,
  );
  const [page, setPage] = useState(1);
  const [sourceFilter, setSourceFilter] = useState("");
  const [successFilter, setSuccessFilter] = useState("");
  const [toolFilter, setToolFilter] = useState("");
  const [groundednessFilter, setGroundednessFilter] = useState("");
  const [approvalStatusFilter, setApprovalStatusFilter] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadAudit = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const summaryData = await apiFetch<AuditSummary>("/api/audit/summary", token);

      if (tab === "tools") {
        const params = new URLSearchParams({
          page: String(page),
          page_size: "25",
        });
        if (sourceFilter) params.set("source", sourceFilter);
        if (successFilter === "true" || successFilter === "false") {
          params.set("success", successFilter);
        }
        if (toolFilter.trim()) params.set("tool_name", toolFilter.trim());
        const toolsData = await apiFetch<PageResponse<ToolAuditRow>>(
          `/api/audit/tools?${params.toString()}`,
          token,
        );
        setTools(toolsData);
      } else if (tab === "runs") {
        const params = new URLSearchParams({
          page: String(page),
          page_size: "25",
        });
        if (groundednessFilter) params.set("groundedness", groundednessFilter);
        const runsData = await apiFetch<PageResponse<RunAuditRow>>(
          `/api/audit/runs?${params.toString()}`,
          token,
        );
        setRuns(runsData);
      } else {
        const params = new URLSearchParams({
          page: String(page),
          page_size: "25",
        });
        if (approvalStatusFilter) params.set("status", approvalStatusFilter);
        const approvalsData = await apiFetch<PageResponse<ApprovalAuditRow>>(
          `/api/audit/approvals?${params.toString()}`,
          token,
        );
        setApprovals(approvalsData);
      }

      setSummary(summaryData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit trail");
    } finally {
      setIsLoading(false);
    }
  }, [
    token,
    tab,
    page,
    sourceFilter,
    successFilter,
    toolFilter,
    groundednessFilter,
    approvalStatusFilter,
  ]);

  useEffect(() => {
    void loadAudit();
  }, [loadAudit]);

  if (!canSeeAudit(roles)) {
    return <Navigate to="/dashboard" replace />;
  }

  function handleTabChange(nextTab: AuditTab) {
    setTab(nextTab);
    setPage(1);
    setExpandedId(null);
  }

  function handleToggleExpanded(rowId: string) {
    setExpandedId((current) => (current === rowId ? null : rowId));
  }

  function handleRefresh() {
    void loadAudit();
  }

  function handlePreviousPage() {
    setPage((current) => Math.max(1, current - 1));
  }

  function handleNextPage(totalPages: number) {
    setPage((current) => Math.min(totalPages, current + 1));
  }

  const activeTotal =
    tab === "tools"
      ? tools?.total ?? 0
      : tab === "runs"
        ? runs?.total ?? 0
        : approvals?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(activeTotal / 25));

  return (
    <div data-testid="audit-page" className="p-6 lg:p-8">
      <PageHeader
        icon={ScrollText}
        title="Audit trail"
        description="Tool calls, agent runs, and HITL approvals from Postgres. Expand a row for Langfuse and GlitchTip when available."
        actions={
          <button
            type="button"
            className="btn-secondary"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        }
      />

      {error ? <p className="error-text mb-4">{error}</p> : null}

      {summary ? (
        <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div className="card p-4">
            <p className="section-label">Tool calls (7d)</p>
            <strong className="mt-1 block font-display text-2xl">
              {summary.tool_calls_7d}
            </strong>
            <p className="mt-1 text-xs text-ink-muted">
              {summary.tool_failures_7d} failed · {summary.native_calls_7d} native ·{" "}
              {summary.mcp_calls_7d} mcp
            </p>
          </div>
          <div className="card p-4">
            <p className="section-label">Agent runs (7d)</p>
            <strong className="mt-1 block font-display text-2xl">
              {summary.agent_runs_7d}
            </strong>
            <p className="mt-1 text-xs text-ink-muted">
              Groundedness{" "}
              {summary.groundedness_pass_rate_7d != null
                ? `${summary.groundedness_pass_rate_7d}%`
                : "—"}
            </p>
          </div>
          <div className="card p-4">
            <p className="section-label">Avg latency</p>
            <strong className="mt-1 block font-display text-2xl">
              {summary.avg_tool_latency_ms != null
                ? `${summary.avg_tool_latency_ms} ms`
                : "—"}
            </strong>
            <p className="mt-1 text-xs text-ink-muted">
              Runs{" "}
              {summary.avg_run_latency_ms != null
                ? `${summary.avg_run_latency_ms} ms`
                : "—"}
            </p>
          </div>
          <div className="card p-4">
            <p className="section-label">HITL approvals (7d)</p>
            <strong className="mt-1 block font-display text-2xl">
              {summary.approvals_pending_7d}
            </strong>
            <p className="mt-1 text-xs text-ink-muted">
              {summary.approvals_approved_7d} approved · {summary.approvals_rejected_7d}{" "}
              rejected
            </p>
          </div>
        </div>
      ) : null}

      <div className="mb-4 flex flex-wrap gap-2">
        {(
          [
            ["tools", "Tool calls"],
            ["runs", "Agent runs"],
            ["approvals", "HITL approvals"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={tab === id ? "btn-primary" : "btn-secondary"}
            onClick={() => handleTabChange(id)}
            data-testid={`audit-tab-${id}`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "tools" ? (
        <div className="mb-4 flex flex-wrap gap-2">
          <select
            className="rounded-xl border border-surface-border bg-white px-3 py-2 text-sm"
            value={sourceFilter}
            onChange={(event) => {
              setSourceFilter(event.target.value);
              setPage(1);
            }}
            data-testid="audit-source-filter"
          >
            <option value="">All sources</option>
            <option value="native">native</option>
            <option value="mcp">mcp</option>
          </select>
          <select
            className="rounded-xl border border-surface-border bg-white px-3 py-2 text-sm"
            value={successFilter}
            onChange={(event) => {
              setSuccessFilter(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All results</option>
            <option value="true">Success</option>
            <option value="false">Failed</option>
          </select>
          <input
            className="min-w-[200px] flex-1 rounded-xl border border-surface-border bg-white px-3 py-2 text-sm"
            placeholder="Filter tool name…"
            value={toolFilter}
            onChange={(event) => {
              setToolFilter(event.target.value);
              setPage(1);
            }}
          />
        </div>
      ) : null}

      {tab === "runs" ? (
        <div className="mb-4">
          <select
            className="rounded-xl border border-surface-border bg-white px-3 py-2 text-sm"
            value={groundednessFilter}
            onChange={(event) => {
              setGroundednessFilter(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All groundedness</option>
            <option value="pass">Passed</option>
            <option value="fail">Failed</option>
            <option value="unset">Unset</option>
          </select>
        </div>
      ) : null}

      {tab === "approvals" ? (
        <div className="mb-4">
          <select
            className="rounded-xl border border-surface-border bg-white px-3 py-2 text-sm"
            value={approvalStatusFilter}
            onChange={(event) => {
              setApprovalStatusFilter(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All statuses</option>
            <option value="pending">pending</option>
            <option value="approved">approved</option>
            <option value="rejected">rejected</option>
          </select>
        </div>
      ) : null}

      <div className="card overflow-hidden">
        {tab === "tools" ? (
          <table className="table">
            <thead>
              <tr>
                <th />
                <th>When</th>
                <th>User</th>
                <th>Tool</th>
                <th>Source</th>
                <th>Result</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {(tools?.items ?? []).map((row) => {
                const expanded = expandedId === row.id;
                return (
                  <Fragment key={row.id}>
                    <tr>
                      <td>
                        <button
                          type="button"
                          className="btn-ghost px-2"
                          onClick={() => handleToggleExpanded(row.id)}
                          aria-expanded={expanded}
                          data-testid={`audit-tool-expand-${row.id}`}
                        >
                          {expanded ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </button>
                      </td>
                      <td className="whitespace-nowrap text-xs">
                        {formatWhen(row.created_at)}
                      </td>
                      <td className="text-xs">{row.user_sub ?? "—"}</td>
                      <td className="mono text-xs">{row.tool_name}</td>
                      <td className="text-xs">{row.source}</td>
                      <td
                        className={
                          row.success ? "text-relay-mint" : "text-relay-danger"
                        }
                      >
                        {row.success ? "Success" : "Failed"}
                      </td>
                      <td>{row.latency_ms != null ? `${row.latency_ms} ms` : "—"}</td>
                    </tr>
                    {expanded ? (
                      <tr>
                        <td colSpan={7} className="bg-surface-muted/40 px-4 py-3">
                          <div className="grid gap-3 text-xs md:grid-cols-2">
                            <div>
                              <p className="section-label mb-1">Request</p>
                              <p className="mono">request_id: {row.request_id ?? "—"}</p>
                              <p className="mono">
                                roles: {(row.user_roles ?? []).join(", ") || "—"}
                              </p>
                            </div>
                            <div>
                              <p className="section-label mb-1">Arguments</p>
                              <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg bg-white p-2">
                                {formatJson(row.arguments)}
                              </pre>
                            </div>
                            <div className="md:col-span-2">
                              <p className="section-label mb-1">Result summary</p>
                              <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg bg-white p-2">
                                {truncate(row.result_summary, 2000)}
                              </pre>
                            </div>
                            <div className="md:col-span-2">
                              <p className="section-label mb-1">Event observability</p>
                              <EventTraceLinks
                                langfuseUrl={row.langfuse_url}
                                glitchtipUrl={row.glitchtip_url}
                              />
                            </div>
                          </div>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        ) : null}

        {tab === "runs" ? (
          <table className="table">
            <thead>
              <tr>
                <th />
                <th>When</th>
                <th>User</th>
                <th>Query</th>
                <th>Groundedness</th>
                <th>Tools</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {(runs?.items ?? []).map((row) => {
                const expanded = expandedId === row.id;
                const groundedLabel =
                  row.groundedness_passed === true
                    ? "Pass"
                    : row.groundedness_passed === false
                      ? "Fail"
                      : "—";
                return (
                  <Fragment key={row.id}>
                    <tr>
                      <td>
                        <button
                          type="button"
                          className="btn-ghost px-2"
                          onClick={() => handleToggleExpanded(row.id)}
                          aria-expanded={expanded}
                        >
                          {expanded ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </button>
                      </td>
                      <td className="whitespace-nowrap text-xs">
                        {formatWhen(row.created_at)}
                      </td>
                      <td className="text-xs">{row.user_sub ?? "—"}</td>
                      <td className="max-w-xs truncate text-sm">{truncate(row.query)}</td>
                      <td
                        className={
                          row.groundedness_passed === true
                            ? "text-relay-mint"
                            : row.groundedness_passed === false
                              ? "text-relay-danger"
                              : "text-ink-muted"
                        }
                      >
                        {groundedLabel}
                      </td>
                      <td className="mono text-xs">
                        {(row.tools_used ?? []).slice(0, 3).join(", ") || "—"}
                      </td>
                      <td>{row.latency_ms != null ? `${row.latency_ms} ms` : "—"}</td>
                    </tr>
                    {expanded ? (
                      <tr>
                        <td colSpan={7} className="bg-surface-muted/40 px-4 py-3">
                          <div className="space-y-3 text-xs">
                            <p className="mono">
                              request_id: {row.request_id ?? "—"} · prompt:{" "}
                              {row.prompt_name ?? "—"} v{row.prompt_version ?? "—"}
                            </p>
                            <div>
                              <p className="section-label mb-1">Query</p>
                              <p className="rounded-lg bg-white p-2">{row.query}</p>
                            </div>
                            <div>
                              <p className="section-label mb-1">Answer</p>
                              <p className="rounded-lg bg-white p-2">
                                {truncate(row.answer, 2000)}
                              </p>
                            </div>
                            <div>
                              <p className="section-label mb-1">Groundedness</p>
                              <p className="rounded-lg bg-white p-2">
                                {row.groundedness_explanation ?? "No explanation stored."}
                              </p>
                            </div>
                            <div>
                              <p className="section-label mb-1">Event observability</p>
                              <EventTraceLinks
                                langfuseUrl={row.langfuse_url}
                                glitchtipUrl={row.glitchtip_url}
                              />
                            </div>
                          </div>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        ) : null}

        {tab === "approvals" ? (
          <table className="table">
            <thead>
              <tr>
                <th />
                <th>When</th>
                <th>Requester</th>
                <th>Tool</th>
                <th>Status</th>
                <th>Decided by</th>
              </tr>
            </thead>
            <tbody>
              {(approvals?.items ?? []).map((row) => {
                const expanded = expandedId === row.id;
                return (
                  <Fragment key={row.id}>
                    <tr>
                      <td>
                        <button
                          type="button"
                          className="btn-ghost px-2"
                          onClick={() => handleToggleExpanded(row.id)}
                          aria-expanded={expanded}
                        >
                          {expanded ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </button>
                      </td>
                      <td className="whitespace-nowrap text-xs">
                        {formatWhen(row.created_at)}
                      </td>
                      <td className="text-xs">{row.created_by_sub}</td>
                      <td className="mono text-xs">{row.tool_name}</td>
                      <td className="capitalize">{row.status}</td>
                      <td className="text-xs">
                        {row.decided_by_sub ?? "—"}
                        {row.decided_at ? ` · ${formatWhen(row.decided_at)}` : ""}
                      </td>
                    </tr>
                    {expanded ? (
                      <tr>
                        <td colSpan={6} className="bg-surface-muted/40 px-4 py-3">
                          <div className="text-xs">
                            <p className="mono mb-2">
                              request_id: {row.request_id} · session: {row.session_id}
                            </p>
                            <p className="section-label mb-1">Proposed arguments</p>
                            <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg bg-white p-2">
                              {formatJson(row.arguments)}
                            </pre>
                            <div className="mt-3">
                              <p className="section-label mb-1">Event observability</p>
                              <EventTraceLinks
                                langfuseUrl={row.langfuse_url}
                                glitchtipUrl={row.glitchtip_url}
                              />
                            </div>
                          </div>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        ) : null}

        {activeTotal === 0 && !isLoading ? (
          <p className="p-6 text-sm text-ink-muted">
            No audit events yet in this view. Use the Assistant (or approve a mutating
            action) — every tool call and agent run is written to Postgres automatically.
          </p>
        ) : null}
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-ink-muted">
        <span>
          {activeTotal} records · page {page} of {totalPages}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            className="btn-secondary py-1 text-xs"
            onClick={handlePreviousPage}
            disabled={page <= 1}
          >
            Previous
          </button>
          <button
            type="button"
            className="btn-secondary py-1 text-xs"
            onClick={() => handleNextPage(totalPages)}
            disabled={page >= totalPages}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
