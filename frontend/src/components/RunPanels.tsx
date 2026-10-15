import { useEffect, useState } from "react";
import {
  Check,
  Circle,
  Clock3,
  Copy,
  Terminal,
  TriangleAlert,
  X,
  BookOpen,
  ArrowUpRight,
} from "lucide-react";
import type { Run, RunStatus, StepEvent } from "../types/run";
const labels: Record<RunStatus, string> = {
  QUEUED: "Queued",
  RUNNING: "Running",
  SUCCEEDED: "Succeeded",
  LIMIT_REACHED: "Step limit reached",
  FAILED: "Failed",
};
export function StatusBadge({ status }: { status: RunStatus }) {
  const Icon =
    status === "SUCCEEDED"
      ? Check
      : status === "FAILED" || status === "LIMIT_REACHED"
        ? TriangleAlert
        : Clock3;
  return (
    <span
      className={`status ${status.toLowerCase()}`}
      role="status"
      aria-live="polite"
    >
      <Icon size={13} />
      {labels[status]}
    </span>
  );
}
export function MetricItem({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
export function RunSummary({ run }: { run: Run | null }) {
  const [tick, setTick] = useState(Date.now());
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    if (!run || run.completed_at) return;
    const timer = setInterval(() => setTick(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [run]);
  const duration = run
    ? Math.max(
        0,
        Math.round(
          ((run.completed_at ? Date.parse(run.completed_at) : tick) -
            Date.parse(run.created_at)) /
            1000,
        ),
      )
    : null;
  return (
    <section className="panel summary" aria-labelledby="summary-title">
      <div className="panel-title">
        <h2 id="summary-title">Run overview</h2>
        <Circle size={14} className="muted" />
      </div>
      <div className="summary-status">
        {run ? (
          <StatusBadge status={run.status} />
        ) : (
          <span className="idle-label">
            <span className="neutral-dot" /> Ready when you are
          </span>
        )}
      </div>
      <p className="muted small">
        {run?.status === "QUEUED"
          ? "Waiting for worker"
          : run?.status === "RUNNING"
            ? "Executing a bounded sequence of actions."
            : run
              ? "Execution complete. Inspect the trace for details."
              : "Your run details will appear here."}
      </p>
      <div className="metrics">
        <MetricItem
          label="Steps used"
          value={run ? `${run.steps_used} / ${run.max_steps}` : "—"}
        />
        <MetricItem
          label="Duration"
          value={duration === null ? "—" : `${duration}s`}
        />
        <MetricItem
          label="Input / output tokens"
          value={
            run?.token_usage
              ? `${run.token_usage.input} / ${run.token_usage.output}`
              : "Not reported"
          }
        />
        <MetricItem label="Execution mode" value={run?.execution_mode || "—"} />
      </div>
      {run?.termination_reason && (
        <div className="reason">
          <span>Termination reason</span>
          <code>{run.termination_reason}</code>
        </div>
      )}
      {run && (
        <button
          className="copy"
          onClick={() => {
            void navigator.clipboard
              .writeText(run.run_id)
              .then(() => setCopied(true))
              .catch(() => setCopied(false));
          }}
          aria-label="Copy run ID"
        >
          <Copy size={13} />
          <span>{copied ? "Copied" : run.run_id.slice(0, 18) + "…"}</span>
        </button>
      )}
      <div className="guardrail">
        <Terminal size={15} />
        <span>
          Bounded by design.
          <br />
          <span className="muted">Every decision has a stopping point.</span>
        </span>
      </div>
    </section>
  );
}
export function StepCard({ step }: { step: StepEvent }) {
  return (
    <li className={step.error ? "step failed-step" : "step"}>
      <span className="step-number">
        {step.error ? <X size={14} /> : step.step_number}
      </span>
      <div className="step-content">
        <div className="step-title">
          <strong>{step.action_summary}</strong>
          <time dateTime={step.timestamp}>
            {new Date(step.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            })}
          </time>
        </div>
        {step.tool_name && <span className="tool-tag">{step.tool_name}</span>}
        {step.error && (
          <p role="alert" className="error-text">
            {step.error}
          </p>
        )}
        {step.observation && (
          <details>
            <summary>
              View tool observation <ArrowUpRight size={12} />
            </summary>
            <pre>
              {step.tool_input &&
                `Input: ${JSON.stringify(step.tool_input)}\n\n`}
              {step.observation}
            </pre>
          </details>
        )}
        {step.source_ids.length > 0 && (
          <p className="source-inline">{step.source_ids.join(" · ")}</p>
        )}
      </div>
    </li>
  );
}
export function ExecutionTimeline({
  steps,
  loading,
}: {
  steps: StepEvent[];
  loading: boolean;
}) {
  return (
    <section className="panel timeline" aria-labelledby="timeline-title">
      <div className="panel-title">
        <h2 id="timeline-title">Execution timeline</h2>
        <span className="small muted">
          {steps.length ? `${steps.length} events` : "ACTION → OBSERVATION"}
        </span>
      </div>
      {steps.length ? (
        <ol>
          {[...steps]
            .sort((a, b) => a.step_number - b.step_number)
            .map((step) => (
              <StepCard key={step.step_number} step={step} />
            ))}
        </ol>
      ) : (
        <div className="empty-timeline">
          <div className="empty-symbol">
            <Terminal size={24} />
          </div>
          <h3>
            {loading
              ? "Waiting for the first action…"
              : "A clear path from question to answer"}
          </h3>
          <p>
            Tool calls, observations, and stopping decisions.
            <br />A concise trace you can inspect.
          </p>
          <div className="mini-flow">
            <span>Decide</span>
            <i>→</i>
            <span>Act</span>
            <i>→</i>
            <span>Observe</span>
          </div>
        </div>
      )}
    </section>
  );
}
export function CitationList({
  ids,
  steps,
}: {
  ids: string[];
  steps: StepEvent[];
}) {
  const entries = steps.flatMap((step) => {
    try {
      const value = JSON.parse(step.observation || "[]");
      return Array.isArray(value) ? value : [];
    } catch {
      return [];
    }
  }) as { id: string; title: string; text: string }[];
  return (
    <div className="citations">
      {ids.map((id) => {
        const entry = entries.find((entry) => entry.id === id);
        return (
          <details key={id}>
            <summary>
              <BookOpen size={13} />
              {id}
              {entry ? ` · ${entry.title}` : ""}
            </summary>
            <p>{entry?.text || "Source ID returned by knowledge search."}</p>
          </details>
        );
      })}
    </div>
  );
}
export function AnswerPanel({
  run,
  steps,
}: {
  run: Run | null;
  steps: StepEvent[];
}) {
  const actual = new Set(steps.flatMap((step) => step.source_ids));
  const ids = (run?.source_ids || []).filter((id) => actual.has(id));
  return (
    <section className="panel answer" aria-labelledby="answer-title">
      <div className="panel-title">
        <h2 id="answer-title">The outcome</h2>
        <BookOpen size={16} className="muted" />
      </div>
      {run?.final_answer ? (
        <>
          <div
            className={`answer-text ${run.termination_reason === "UNSUPPORTED" ? "evidence-warning" : ""}`}
          >
            {run.final_answer}
          </div>
          {run.termination_reason === "UNSUPPORTED" && (
            <p className="small error-text">
              Evidence insufficient · this answer is unsupported.
            </p>
          )}
          <CitationList ids={ids} steps={steps} />
        </>
      ) : (
        <p className="muted answer-empty">
          A final answer, grounded in retrieved evidence, will appear when the
          run finishes.
        </p>
      )}
    </section>
  );
}
export function FeedbackBanner({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss?: () => void;
}) {
  return (
    <div className="feedback" role="alert">
      <TriangleAlert size={16} />
      <span>{message}</span>
      {onDismiss && (
        <button aria-label="Dismiss error" onClick={onDismiss}>
          <X size={16} />
        </button>
      )}
    </div>
  );
}
