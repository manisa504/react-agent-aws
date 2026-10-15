import { fetchAuthSession } from "aws-amplify/auth";
import { config } from "./config";
import type { Run, StepEvent } from "../types/run";
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
async function request<T>(
  path: string,
  init: RequestInit = {},
  signal?: AbortSignal,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (!config.demo) {
    const token = (await fetchAuthSession()).tokens?.accessToken.toString();
    if (!token) throw new ApiError(401, "Your session expired. Sign in again.");
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(`${config.api}${path}`, {
    ...init,
    headers,
    signal,
  });
  if (!response.ok)
    throw new ApiError(
      response.status,
      response.status === 401
        ? "Your session expired. Sign in again."
        : response.status === 403
          ? "Access denied."
          : response.status === 404
            ? "This run is unavailable."
            : response.status === 422
              ? "Check your task and step limit."
              : "The API could not complete the request.",
    );
  return response.json();
}
export const api = {
  create: (task: string, max_steps: number) =>
    request<{ run_id: string; status: "QUEUED" }>("/runs", {
      method: "POST",
      body: JSON.stringify({ task, max_steps }),
    }),
  run: (id: string, signal: AbortSignal) =>
    request<Run>(`/runs/${encodeURIComponent(id)}`, {}, signal),
  steps: (id: string, signal: AbortSignal) =>
    request<StepEvent[]>(`/runs/${encodeURIComponent(id)}/steps`, {}, signal),
};
