import { CheckCircle2, Circle, FlaskConical, Loader2, Play, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import { canRunEvals } from "../lib/rbac";
import { useAuth } from "../providers/AuthProvider";
import type { EvalRunStatus, EvalStep } from "../types/evaluations";

type SuiteResponse = {
  suite_name: string;
  total: number;
  questions: Array<{
    id: string;
    role: string;
    query: string;
    notes?: string;
  }>;
};

type HistoryResponse = {
  summary: { total: number; passed: number; avg_latency_ms: number | null };
  items: Array<{
    id: string;
    suite_name: string;
    question_id: string;
    role_name: string;
    passed: boolean;
    score: number | null;
    latency_ms: number | null;
  }>;
  run_status?: EvalRunStatus;
};

function StepIcon({ status }: { status: EvalStep["status"] }) {
  if (status === "running") {
    return <Loader2 className="h-4 w-4 animate-spin text-relay-cyan" aria-hidden />;
  }
  if (status === "passed") {
    return <CheckCircle2 className="h-4 w-4 text-relay-mint" aria-hidden />;
  }
  if (status === "failed") {
    return <XCircle className="h-4 w-4 text-relay-danger" aria-hidden />;
  }
  return <Circle className="h-4 w-4 text-ink-muted" aria-hidden />;
}

export function EvaluationsPage() {
  const { token, roles } = useAuth();
  const [suite, setSuite] = useState<SuiteResponse | null>(null);
  const [runStatus, setRunStatus] = useState<EvalRunStatus | null>(null);
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const refreshHistory = useCallback(async () => {
    if (!token) {
      return;
    }
    const data = await apiFetch<HistoryResponse>("/api/evaluations/runs", token);
    setHistory(data);
    if (data.run_status) {
      setRunStatus(data.run_status);
    }
  }, [token]);

  const refreshStatus = useCallback(async () => {
    if (!token) {
      return;
    }
    const status = await apiFetch<EvalRunStatus>("/api/evaluations/run/status", token);
    setRunStatus(status);
    return status;
  }, [token]);

  useEffect(() => {
    if (!token || !canRunEvals(roles)) {
      setIsLoading(false);
      return;
    }
    const accessToken = token;

    async function loadEvaluationsPage() {
      setIsLoading(true);
      try {
        const [suiteData] = await Promise.all([
          apiFetch<SuiteResponse>("/api/evaluations/suite", accessToken),
          refreshHistory(),
          refreshStatus(),
        ]);
        setSuite(suiteData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load evaluations");
      } finally {
        setIsLoading(false);
      }
    }

    void loadEvaluationsPage();
  }, [token, roles, refreshHistory, refreshStatus]);

  useEffect(() => {
    if (!token || runStatus?.status !== "running") {
      return;
    }
    const timer = window.setInterval(() => {
      void refreshStatus()
        .then((status) => {
          if (status && (status.status === "completed" || status.status === "failed")) {
            void refreshHistory();
          }
        })
        .catch((err: Error) => setError(err.message));
    }, 1500);
    return () => window.clearInterval(timer);
  }, [token, runStatus?.status, refreshStatus, refreshHistory]);

  async function handleStartRun() {
    if (!token) {
      return;
    }
    setIsStarting(true);
    setError(null);
    try {
      const status = await apiFetch<EvalRunStatus>("/api/evaluations/run", token, {
        method: "POST",
      });
      setRunStatus(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start evaluation");
    } finally {
      setIsStarting(false);
    }
  }

  if (!canRunEvals(roles)) {
    return <Navigate to="/assistant" replace />;
  }

  const isRunning = runStatus?.status === "running";
  const steps = runStatus?.steps?.length
    ? runStatus.steps
    : (suite?.questions ?? []).map((question, index) => ({
        step: index + 1,
        label: `Step ${index + 1} of ${suite?.total ?? 0}`,
        question_id: question.id,
        role: question.role,
        query: question.query,
        status: "pending" as const,
        passed: null,
        latency_ms: null,
        tools_used: [],
        error: null,
        answer_preview: null,
      }));

  return (
    <div data-testid="evaluations-page" className="space-y-6 p-6 lg:p-8">
      <PageHeader
        icon={FlaskConical}
        title="Evaluations"
        description="Run the live Relay eval suite from the desk. The suite runs asynchronously on the API — leaving this page or switching tabs does not stop it. Each question is a numbered step with pass/fail scoring."
        actions={
          <button
            type="button"
            className="btn-primary"
            onClick={() => void handleStartRun()}
            disabled={isStarting || isRunning || isLoading}
            data-testid="eval-run-button"
          >
            {isRunning || isStarting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Running…
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Run suite
              </>
            )}
          </button>
        }
      />

      {error ? <p className="error-text">{error}</p> : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="card p-4">
          <p className="section-label">Suite size</p>
          <strong className="mt-1 block font-display text-2xl">
            {runStatus?.total || suite?.total || "—"}
          </strong>
        </div>
        <div className="card p-4">
          <p className="section-label">Progress</p>
          <strong className="mt-1 block font-display text-2xl">
            {runStatus ? `${runStatus.progress}/${runStatus.total || "—"}` : "—"}
          </strong>
        </div>
        <div className="card p-4">
          <p className="section-label">Passed (this run)</p>
          <strong className="mt-1 block font-display text-2xl">
            {runStatus?.summary?.passed ?? "—"}
          </strong>
        </div>
        <div className="card p-4">
          <p className="section-label">Avg latency</p>
          <strong className="mt-1 block font-display text-2xl">
            {runStatus?.summary?.avg_latency_ms != null
              ? `${runStatus.summary.avg_latency_ms} ms`
              : history?.summary.avg_latency_ms != null
                ? `${history.summary.avg_latency_ms} ms`
                : "—"}
          </strong>
        </div>
      </div>

      {runStatus?.current_step ? (
        <div
          className="card border-l-4 border-l-relay-cyan p-4"
          data-testid="eval-current-step"
        >
          <p className="section-label">Current step</p>
          <p className="mt-1 font-display text-lg font-semibold text-ink-primary">
            {runStatus.current_step}
          </p>
          {runStatus.error ? (
            <p className="mt-2 text-sm text-relay-danger">{runStatus.error}</p>
          ) : null}
        </div>
      ) : null}

      <section className="card overflow-hidden" data-testid="eval-steps">
        <div className="border-b border-surface-border px-4 py-3">
          <h2 className="font-display text-lg font-semibold">Suite steps</h2>
          <p className="mt-1 text-sm text-ink-secondary">
            Each step runs one eval question as the seeded role (sales / support / admin).
            Progress continues on the server if you navigate away.
          </p>
        </div>
        <ol className="divide-y divide-surface-border">
          {steps.map((step) => (
            <li
              key={step.question_id}
              className="px-4 py-4"
              data-testid={`eval-step-${step.question_id}`}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5">
                  <StepIcon status={step.status} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold text-ink-primary">
                      Step {step.step}
                      {suite?.total || runStatus?.total
                        ? ` of ${suite?.total || runStatus?.total}`
                        : ""}
                    </p>
                    <span className="mono text-xs text-ink-muted">{step.question_id}</span>
                    <span className="text-xs uppercase tracking-wide text-ink-muted">
                      {step.role}
                    </span>
                    <span
                      className={
                        step.status === "passed"
                          ? "text-xs font-semibold text-relay-mint"
                          : step.status === "failed"
                            ? "text-xs font-semibold text-relay-danger"
                            : step.status === "running"
                              ? "text-xs font-semibold text-relay-cyan"
                              : "text-xs text-ink-muted"
                      }
                    >
                      {step.status}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-ink-secondary">{step.query}</p>
                  {step.tools_used.length > 0 ? (
                    <p className="mt-2 mono text-xs text-ink-muted">
                      tools: {step.tools_used.join(", ")}
                      {step.latency_ms != null ? ` · ${step.latency_ms} ms` : ""}
                    </p>
                  ) : null}
                  {step.error ? (
                    <p className="mt-2 text-sm text-relay-danger">{step.error}</p>
                  ) : null}
                  {step.answer_preview ? (
                    <p className="mt-2 text-sm text-ink-secondary">{step.answer_preview}</p>
                  ) : null}
                </div>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {history && history.items.length > 0 ? (
        <section className="card overflow-hidden">
          <div className="border-b border-surface-border px-4 py-3">
            <h2 className="font-display text-lg font-semibold">Recent results</h2>
            <p className="mt-1 text-sm text-ink-secondary">
              Persisted rows from Postgres ({history.summary.passed}/{history.summary.total}{" "}
              passed historically).
            </p>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Question</th>
                <th>Role</th>
                <th>Passed</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {history.items.slice(0, 20).map((item) => (
                <tr key={item.id}>
                  <td className="mono text-xs">{item.question_id}</td>
                  <td>{item.role_name}</td>
                  <td>{item.passed ? "yes" : "no"}</td>
                  <td>{item.latency_ms != null ? `${item.latency_ms} ms` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}
    </div>
  );
}
