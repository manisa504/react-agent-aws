export type RunStatus =
  | "QUEUED"
  | "RUNNING"
  | "SUCCEEDED"
  | "LIMIT_REACHED"
  | "FAILED";
export type TerminationReason =
  | "FINAL_ANSWER"
  | "STEP_LIMIT"
  | "UNSUPPORTED"
  | "MODEL_ERROR"
  | "TOOL_ERROR"
  | "TIMEOUT"
  | "INVALID_TOOL";
export type Run = {
  run_id: string;
  status: RunStatus;
  execution_mode: "MOCK" | "BEDROCK";
  max_steps: number;
  steps_used: number;
  token_usage?: { input: number; output: number } | null;
  termination_reason?: TerminationReason | null;
  final_answer?: string | null;
  source_ids: string[];
  created_at: string;
  completed_at?: string | null;
};
export type StepEvent = {
  step_number: number;
  timestamp: string;
  action_summary: string;
  tool_name?: "calculator" | "knowledge_search" | null;
  tool_input?: Record<string, unknown> | null;
  observation?: string | null;
  source_ids: string[];
  error?: string | null;
};
export const terminal = (status: RunStatus) =>
  ["SUCCEEDED", "LIMIT_REACHED", "FAILED"].includes(status);
