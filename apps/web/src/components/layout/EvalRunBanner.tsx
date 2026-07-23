import { FlaskConical, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

import type { EvalRunStatus } from "../../types/evaluations";

type EvalRunBannerProps = {
  runStatus: EvalRunStatus;
};

export function EvalRunBanner({ runStatus }: EvalRunBannerProps) {
  const progressLabel =
    runStatus.total > 0
      ? `${runStatus.progress}/${runStatus.total}`
      : String(runStatus.progress);

  return (
    <div
      className="border-b border-relay-cyan/30 bg-relay-cyan/10 px-4 py-2.5"
      data-testid="eval-run-banner"
      role="status"
    >
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2 text-sm text-ink-primary">
          <Loader2 className="h-4 w-4 shrink-0 animate-spin text-relay-cyan" aria-hidden />
          <FlaskConical className="h-4 w-4 shrink-0 text-relay-cyan" aria-hidden />
          <span>
            Eval suite running on the server ({progressLabel})
            {runStatus.current_step ? ` · ${runStatus.current_step}` : ""}
          </span>
        </div>
        <Link
          to="/evaluations"
          className="text-sm font-semibold text-relay-cyan hover:underline"
        >
          View steps
        </Link>
      </div>
    </div>
  );
}
