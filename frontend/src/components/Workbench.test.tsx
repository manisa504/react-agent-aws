import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { TaskComposer } from "./TaskComposer";
import {
  AnswerPanel,
  ExecutionTimeline,
  FeedbackBanner,
  RunSummary,
  StatusBadge,
} from "./RunPanels";
import type { Run, StepEvent } from "../types/run";

const run: Run = {
  run_id: "example",
  status: "SUCCEEDED",
  execution_mode: "MOCK",
  max_steps: 5,
  steps_used: 3,
  created_at: "2026-10-15T10:00:00Z",
  completed_at: "2026-10-15T10:00:03Z",
  final_answer: "Result: 7200 [AWS-SQS]",
  source_ids: ["AWS-SQS", "INVENTED"],
  termination_reason: "FINAL_ANSWER",
};
const steps: StepEvent[] = [
  {
    step_number: 1,
    timestamp: run.created_at,
    action_summary: "Execute knowledge_search",
    tool_name: "knowledge_search",
    observation: '[{"id":"AWS-SQS","title":"SQS","text":"Curated evidence"}]',
    source_ids: ["AWS-SQS"],
  },
];

test("composer validates input and sample selection never submits", async () => {
  const submit = vi.fn().mockResolvedValue(undefined);
  render(<TaskComposer onSubmit={submit} isSubmitting={false} />);
  expect(screen.getByRole("button", { name: "Run task" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "AWS decision" }));
  expect(submit).not.toHaveBeenCalled();
  expect(screen.getByLabelText("Planning task")).toHaveAttribute(
    "maxlength",
    "2000",
  );
  expect(screen.getByLabelText("Step limit")).toHaveValue("5");
  fireEvent.click(screen.getByRole("button", { name: "Run task" }));
  await waitFor(() =>
    expect(submit).toHaveBeenCalledWith(expect.stringContaining("photo"), 5),
  );
});
test("submitting prevents duplicate submission", () => {
  render(<TaskComposer onSubmit={vi.fn()} isSubmitting />);
  expect(screen.getByRole("button", { name: "Starting…" })).toBeDisabled();
});
test("timeline renders sorted accessible observations", () => {
  render(
    <ExecutionTimeline
      steps={[
        { ...steps[0], step_number: 2, action_summary: "Second" },
        steps[0],
      ]}
      loading={false}
    />,
  );
  const items = screen.getAllByRole("listitem");
  expect(items[0]).toHaveTextContent("Execute knowledge_search");
  expect(items[1]).toHaveTextContent("Second");
  expect(screen.getAllByText(/View tool observation/)).toHaveLength(2);
});
test("empty running state", () => {
  render(<ExecutionTimeline steps={[]} loading />);
  expect(screen.getByText("Waiting for the first action…")).toBeInTheDocument();
});
test("mode and actual metrics", () => {
  render(<RunSummary run={run} />);
  expect(screen.getByText("MOCK")).toBeInTheDocument();
  expect(screen.getByText("Not reported")).toBeInTheDocument();
  expect(screen.getByText("3 / 5")).toBeInTheDocument();
});
test("answer citations are restricted to observed evidence", () => {
  render(<AnswerPanel run={run} steps={steps} />);
  expect(screen.getByText("AWS-SQS · SQS")).toBeInTheDocument();
  expect(screen.queryByText("INVENTED")).not.toBeInTheDocument();
});
test("unsupported answer is labelled", () => {
  render(
    <AnswerPanel
      run={{ ...run, status: "FAILED", termination_reason: "UNSUPPORTED" }}
      steps={steps}
    />,
  );
  expect(screen.getByText(/Evidence insufficient/)).toBeInTheDocument();
});
test("step limit and failure are text statuses", () => {
  render(
    <>
      <StatusBadge status="LIMIT_REACHED" />
      <StatusBadge status="FAILED" />
    </>,
  );
  expect(screen.getByText("Step limit reached")).toBeInTheDocument();
  expect(screen.getByText("Failed")).toBeInTheDocument();
});
test("errors announce and dismiss", () => {
  const dismiss = vi.fn();
  render(<FeedbackBanner message="Network failed" onDismiss={dismiss} />);
  expect(screen.getByRole("alert")).toHaveTextContent("Network failed");
  fireEvent.click(screen.getByRole("button", { name: "Dismiss error" }));
  expect(dismiss).toHaveBeenCalledOnce();
});
test("answer is rendered as text", () => {
  render(
    <AnswerPanel
      run={{ ...run, final_answer: "<script>bad()</script>" }}
      steps={[]}
    />,
  );
  expect(screen.getByText("<script>bad()</script>")).toBeInTheDocument();
  expect(document.querySelector("script")).toBeNull();
});
