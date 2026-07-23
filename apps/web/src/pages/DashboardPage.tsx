import { Building2, LayoutDashboard, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  MetricsLineChart,
  PriorityBarChart,
  RiskBarChart,
  SimpleBarChart,
  type ChartPoint,
  type TimeSeriesPoint,
} from "../components/dashboard/DeskCharts";
import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import { canViewOrgWideInsights } from "../lib/rbac";
import { useAuth } from "../providers/AuthProvider";

type Summary = {
  open_cases: number;
  critical_cases: number;
  pending_actions: number;
  active_accounts: number;
  sla_breach_risk: number;
  open_tasks: number;
  groundedness_pass_rate_7d: number | null;
  customers_at_risk: number;
  customers_high_risk: number;
  renewals_at_risk: number;
  contract_value_at_risk_gbp: number;
  charts: {
    by_priority: ChartPoint[];
    by_status: ChartPoint[];
    risk_by_account: ChartPoint[];
  };
  role_scope: string[];
};

type TimeseriesResponse = {
  metric: string;
  points: TimeSeriesPoint[];
};

type RenewalItem = {
  external_id: string;
  name: string;
  renewal_date: string;
  days_until_renewal: number;
  open_issues: number;
  contract_value_gbp: number | null;
  risk_status: string;
};

function formatGbp(value: number): string {
  if (value >= 1_000_000) return `£${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `£${Math.round(value / 1_000)}K`;
  return `£${value}`;
}

export function DashboardPage() {
  const { token, roles } = useAuth();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [openTrend, setOpenTrend] = useState<TimeSeriesPoint[]>([]);
  const [riskTrend, setRiskTrend] = useState<TimeSeriesPoint[]>([]);
  const [renewals, setRenewals] = useState<RenewalItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadDashboard = useCallback(async () => {
    if (!token) {
      return;
    }
    setIsLoading(true);
    try {
      const [summaryData, openSeries, riskSeries, renewalData] = await Promise.all([
        apiFetch<Summary>("/api/desk/summary", token),
        apiFetch<TimeseriesResponse>(
          "/api/desk/metrics/timeseries?metric=open_issues&days=30",
          token,
        ),
        apiFetch<TimeseriesResponse>(
          "/api/desk/metrics/timeseries?metric=customers_at_risk&days=30",
          token,
        ),
        apiFetch<{ items: RenewalItem[] }>("/api/desk/renewal-risk", token),
      ]);
      setSummary(summaryData);
      setOpenTrend(openSeries.points);
      setRiskTrend(riskSeries.points);
      setRenewals(renewalData.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  function handleRefresh() {
    void loadDashboard();
  }

  const kpis = [
    {
      label: "Customers at risk",
      value: summary?.customers_at_risk,
      tone: "warn" as const,
    },
    {
      label: "High risk accounts",
      value: summary?.customers_high_risk,
      tone: "danger" as const,
    },
    {
      label: "Renewals at risk",
      value: summary?.renewals_at_risk,
      tone: "warn" as const,
    },
    {
      label: "Contract at risk",
      value:
        summary?.contract_value_at_risk_gbp != null
          ? formatGbp(summary.contract_value_at_risk_gbp)
          : undefined,
      tone: "danger" as const,
    },
    { label: "Open cases", value: summary?.open_cases, tone: "default" as const },
    {
      label: "Critical cases",
      value: summary?.critical_cases,
      tone: "danger" as const,
    },
    {
      label: "Pending actions",
      value: summary?.pending_actions,
      tone: "warn" as const,
    },
    {
      label: "SLA risk (4h)",
      value: summary?.sla_breach_risk,
      tone: "warn" as const,
    },
  ];

  const scopeSuffix = summary?.role_scope?.length
    ? ` (${summary.role_scope.join(", ")})`
    : "";

  return (
    <div data-testid="dashboard-page" className="space-y-6 p-6 lg:p-8">
      <PageHeader
        icon={LayoutDashboard}
        title="Command dashboard"
        description={`Account management + support KPIs${scopeSuffix}.`}
        actions={
          <>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleRefresh}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </button>
            <Link className="btn-primary" to="/assistant">
              Open assistant
            </Link>
          </>
        }
      />

      {error ? <p className="error-text">{error}</p> : null}

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {kpis.map((kpi) => (
            <div key={kpi.label} className="card p-4">
              <p className="section-label">{kpi.label}</p>
              <strong
                className={
                  kpi.tone === "danger"
                    ? "mt-1 block font-display text-2xl font-semibold text-relay-danger"
                    : kpi.tone === "warn"
                      ? "mt-1 block font-display text-2xl font-semibold text-relay-warn"
                      : "mt-1 block font-display text-2xl font-semibold text-ink-primary"
                }
              >
                {kpi.value ?? "—"}
              </strong>
            </div>
          ))}
          {canViewOrgWideInsights(roles) ? (
            <div className="card p-4">
              <p className="section-label">Groundedness (7d)</p>
              <strong className="mt-1 block font-display text-2xl font-semibold text-relay-mint">
                {summary?.groundedness_pass_rate_7d != null
                  ? `${summary.groundedness_pass_rate_7d}%`
                  : "—"}
              </strong>
            </div>
          ) : null}
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          <MetricsLineChart
            title="Open issues trend (30 days)"
            data={openTrend}
            seriesName="Open issues"
            testId="chart-open-issues-trend"
          />
          <MetricsLineChart
            title="Customers at risk trend (30 days)"
            data={riskTrend}
            seriesName="At risk"
            testId="chart-customers-at-risk-trend"
          />
        </div>

        <div className="grid gap-4 xl:grid-cols-3">
          <PriorityBarChart
            title="Open cases by priority"
            data={summary?.charts.by_priority ?? []}
            testId="chart-by-priority"
          />
          <SimpleBarChart
            title="Cases by status"
            data={summary?.charts.by_status ?? []}
            testId="chart-by-status"
          />
          <RiskBarChart
            title="Account risk scores"
            data={summary?.charts.risk_by_account ?? []}
            testId="chart-risk-by-account"
          />
        </div>

        <div className="card overflow-hidden" data-testid="renewal-risk-panel">
          <div className="flex items-center gap-2 border-b border-surface-border px-4 py-3">
            <Building2 className="h-4 w-4 text-relay-cyan" />
            <h2 className="text-sm font-semibold text-ink-primary">Renewals in next 120 days</h2>
          </div>
          {renewals.length === 0 ? (
            <p className="p-4 text-sm text-ink-muted">No renewals in the window.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Account</th>
                  <th>Renewal</th>
                  <th>Days</th>
                  <th>Open</th>
                  <th>Contract</th>
                  <th>Risk</th>
                </tr>
              </thead>
              <tbody>
                {renewals.map((item) => (
                  <tr key={item.external_id}>
                    <td className="font-medium">{item.name}</td>
                    <td className="mono text-xs">{item.renewal_date}</td>
                    <td>{item.days_until_renewal}</td>
                    <td>{item.open_issues}</td>
                    <td>
                      {item.contract_value_gbp != null
                        ? formatGbp(item.contract_value_gbp)
                        : "—"}
                    </td>
                    <td className="capitalize text-ink-secondary">{item.risk_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
    </div>
  );
}
