import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../lib/api";
import { canRunEvals } from "../lib/rbac";
import type { EvalRunStatus } from "../types/evaluations";

const IDLE_POLL_MS = 8000;
const RUNNING_POLL_MS = 1500;

export function useEvalRunMonitor(token: string | null, roles: string[]) {
  const [runStatus, setRunStatus] = useState<EvalRunStatus | null>(null);
  const allowed = Boolean(token && canRunEvals(roles));

  const refreshStatus = useCallback(async () => {
    if (!token || !canRunEvals(roles)) {
      return null;
    }
    const status = await apiFetch<EvalRunStatus>("/api/evaluations/run/status", token);
    setRunStatus(status);
    return status;
  }, [token, roles]);

  useEffect(() => {
    if (!allowed) {
      setRunStatus(null);
      return;
    }

    let cancelled = false;
    let timerId = 0;

    async function pollOnce() {
      try {
        const status = await refreshStatus();
        if (cancelled) {
          return;
        }
        const delay =
          status?.status === "running" ? RUNNING_POLL_MS : IDLE_POLL_MS;
        timerId = window.setTimeout(() => {
          void pollOnce();
        }, delay);
      } catch {
        if (cancelled) {
          return;
        }
        timerId = window.setTimeout(() => {
          void pollOnce();
        }, IDLE_POLL_MS);
      }
    }

    void pollOnce();
    return () => {
      cancelled = true;
      window.clearTimeout(timerId);
    };
  }, [allowed, refreshStatus]);

  return {
    runStatus,
    isRunning: runStatus?.status === "running",
    refreshStatus,
  };
}
