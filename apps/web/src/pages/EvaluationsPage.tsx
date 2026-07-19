import { useEffect, useState } from "react";

import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type EvalRun = {
  id: string;
  suite_name: string;
  question_id: string;
  role_name: string;
  passed: boolean;
  score: number | null;
  latency_ms: number | null;
};

type EvalResponse = {
  summary: { total: number; passed: number; avg_latency_ms: number | null };
  items: EvalRun[];
};

export function EvaluationsPage() {
  const { token } = useAuth();
  const [data, setData] = useState<EvalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    void apiFetch<EvalResponse>("/api/evaluations/runs", token)
      .then((response) => {
        setData(response);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, [token]);

  return (
    <div data-testid="evaluations-page">
      <h1>Evaluations</h1>
      <p className="page-lead">
        Offline eval suite results. Run <code>make eval-host</code> to populate.
      </p>
      {error ? <p className="error-text">{error}</p> : null}
      <div className="grid-3">
        <div className="stat">
          Total
          <strong>{data?.summary.total ?? "—"}</strong>
        </div>
        <div className="stat">
          Passed
          <strong>{data?.summary.passed ?? "—"}</strong>
        </div>
        <div className="stat">
          Avg latency
          <strong>
            {data?.summary.avg_latency_ms != null ? `${data.summary.avg_latency_ms} ms` : "—"}
          </strong>
        </div>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Suite</th>
            <th>Question</th>
            <th>Role</th>
            <th>Passed</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {(data?.items ?? []).map((run) => (
            <tr key={run.id}>
              <td>{run.suite_name}</td>
              <td>{run.question_id}</td>
              <td>{run.role_name}</td>
              <td>{run.passed ? "yes" : "no"}</td>
              <td>{run.score ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
