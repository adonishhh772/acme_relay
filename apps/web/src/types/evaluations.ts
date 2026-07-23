export type EvalStepStatus = "pending" | "running" | "passed" | "failed";

export type EvalStep = {
  step: number;
  label: string;
  question_id: string;
  role: string;
  query: string;
  status: EvalStepStatus;
  passed: boolean | null;
  latency_ms: number | null;
  tools_used: string[];
  error: string | null;
  answer_preview: string | null;
};

export type EvalRunStatus = {
  status: "idle" | "running" | "completed" | "failed";
  suite_name: string;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
  progress: number;
  total: number;
  current_step: string | null;
  steps: EvalStep[];
  summary: {
    total: number;
    passed: number;
    failed: number;
    pass_rate: number;
    tool_selection_pass: number;
    groundedness_pass: number;
    rbac_pass: number;
    next_action_pass: number;
    avg_latency_ms: number | null;
  } | null;
};
