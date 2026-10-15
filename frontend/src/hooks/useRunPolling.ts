import { useEffect, useState } from "react";
import { api, ApiError } from "../lib/api";
import { terminal, type Run, type StepEvent } from "../types/run";
export function useRunPolling(id: string | null) {
  const [run, setRun] = useState<Run | null>(null);
  const [steps, setSteps] = useState<StepEvent[]>([]);
  const [error, setError] = useState("");
  const [unauthorized, setUnauthorized] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    setRun(null);
    setSteps([]);
    setError("");
    setUnauthorized(false);
    if (!id) return;
    let alive = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const controller = new AbortController();
    async function poll() {
      try {
        // Status first, then steps, so a terminal read includes the final event.
        const next = await api.run(id!, controller.signal);
        const events = await api.steps(id!, controller.signal);
        if (!alive) return;
        setRun(next);
        setSteps(events);
        if (!terminal(next.status)) timer = setTimeout(poll, 2000);
      } catch (e) {
        if (!alive) return;
        setError(e instanceof Error ? e.message : "Network unavailable.");
        setUnauthorized(e instanceof ApiError && e.status === 401);
      }
    }
    void poll();
    return () => {
      alive = false;
      controller.abort();
      clearTimeout(timer);
    };
  }, [id, attempt]);
  return {
    run,
    steps,
    error,
    unauthorized,
    reconnect: () => setAttempt((n) => n + 1),
  };
}
