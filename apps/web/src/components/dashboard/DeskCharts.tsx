import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type ChartPoint = {
  label: string;
  value: number;
  status?: string;
};

export type TimeSeriesPoint = {
  date: string;
  value: number;
};

const PRIORITY_COLORS: Record<string, string> = {
  critical: "#e11d48",
  high: "#d97706",
  medium: "#0891b2",
  low: "#64748b",
};

const RISK_COLORS: Record<string, string> = {
  red: "#e11d48",
  amber: "#d97706",
  green: "#14b8a6",
};

type SimpleBarChartProps = {
  title: string;
  data: ChartPoint[];
  testId?: string;
};

export function SimpleBarChart({ title, data, testId }: SimpleBarChartProps) {
  return (
    <div className="card p-4" data-testid={testId}>
      <p className="section-label">{title}</p>
      <div className="mt-3 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="value" radius={[6, 6, 0, 0]} fill="#0891b2" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

type PriorityBarChartProps = {
  title: string;
  data: ChartPoint[];
  testId?: string;
};

export function PriorityBarChart({ title, data, testId }: PriorityBarChartProps) {
  return (
    <div className="card p-4" data-testid={testId}>
      <p className="section-label">{title}</p>
      <div className="mt-3 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              {data.map((entry) => (
                <Cell
                  key={entry.label}
                  fill={PRIORITY_COLORS[entry.label] ?? "#0891b2"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

type RiskBarChartProps = {
  title: string;
  data: ChartPoint[];
  testId?: string;
};

export function RiskBarChart({ title, data, testId }: RiskBarChartProps) {
  return (
    <div className="card p-4" data-testid={testId}>
      <p className="section-label">{title}</p>
      <div className="mt-3 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              {data.map((entry) => (
                <Cell
                  key={entry.label}
                  fill={RISK_COLORS[entry.status ?? "green"] ?? "#14b8a6"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

type MetricsLineChartProps = {
  title: string;
  data: TimeSeriesPoint[];
  seriesName: string;
  testId?: string;
};

export function MetricsLineChart({
  title,
  data,
  seriesName,
  testId,
}: MetricsLineChartProps) {
  const chartData = data.map((point) => ({
    date: point.date.slice(5),
    [seriesName]: point.value,
  }));

  return (
    <div className="card p-4" data-testid={testId}>
      <p className="section-label">{title}</p>
      <div className="mt-3 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Line
              type="monotone"
              dataKey={seriesName}
              stroke="#0891b2"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
