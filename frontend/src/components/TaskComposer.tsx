import { useState } from "react";
import {
  ArrowUpRight,
  Sparkles,
  Calculator,
  CircleHelp,
  Repeat2,
  LoaderCircle,
} from "lucide-react";
export const samples = [
  {
    label: "AWS decision",
    icon: Sparkles,
    task: "For a small photo-processing workflow, should I use SQS or EventBridge? Also calculate how many images arrive in 15 minutes at 8 images per second.",
  },
  {
    label: "Calculation",
    icon: Calculator,
    task: "Compare SQS and EventBridge. Calculate: (120 * 30) / 4",
  },
  {
    label: "Unsupported",
    icon: CircleHelp,
    task: "[unsupported] What is the exact AWS bill for my account today?",
  },
  {
    label: "Bounded loop",
    icon: Repeat2,
    task: "[loop] Demonstrate an agent repeatedly requesting a calculation until its step limit.",
  },
];
export function SamplePromptChips({
  onSelect,
}: {
  onSelect: (task: string) => void;
}) {
  return (
    <div className="samples">
      <span>Try a scenario</span>
      {samples.map(({ label, icon: Icon, task }) => (
        <button key={label} type="button" onClick={() => onSelect(task)}>
          <Icon size={14} />
          {label}
        </button>
      ))}
    </div>
  );
}
export function TaskComposer({
  onSubmit,
  isSubmitting,
  disabled = false,
}: {
  onSubmit: (task: string, maxSteps: number) => Promise<void>;
  isSubmitting: boolean;
  disabled?: boolean;
}) {
  const [task, setTask] = useState("");
  const [limit, setLimit] = useState(5);
  return (
    <section className="composer panel" aria-labelledby="composer-title">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (task.trim() && !disabled) void onSubmit(task.trim(), limit);
        }}
      >
        <div className="section-label">
          <span id="composer-title">YOUR TASK</span>
          <span className="small muted">
            Two safe tools. One clear outcome.
          </span>
        </div>
        <label className="sr-only" htmlFor="task">
          Planning task
        </label>
        <textarea
          id="task"
          placeholder="What would you like to work through?"
          value={task}
          maxLength={2000}
          onChange={(e) => setTask(e.target.value)}
          disabled={disabled}
        />
        <div className="composer-controls">
          <div className="limit-control">
            <span className="live-dot" />
            <label htmlFor="steps">Step limit</label>
            <select
              id="steps"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              disabled={disabled}
            >
              {[3, 4, 5, 6, 7, 8].map((n) => (
                <option key={n}>{n}</option>
              ))}
            </select>
            <span className="muted small">Max. 8</span>
          </div>
          <div className="submit-group">
            <span className="counter">
              {task.length.toLocaleString()} / 2,000
            </span>
            <button
              className="primary"
              type="submit"
              disabled={!task.trim() || isSubmitting || disabled}
            >
              {isSubmitting ? (
                <LoaderCircle className="spin" size={16} />
              ) : (
                <ArrowUpRight size={17} />
              )}{" "}
              {isSubmitting ? "Starting…" : "Run task"}
            </button>
          </div>
        </div>
      </form>
      <SamplePromptChips
        onSelect={(task) => {
          if (!disabled) setTask(task);
        }}
      />
    </section>
  );
}
