import { act, renderHook, waitFor } from "@testing-library/react";
import { api, ApiError } from "../lib/api";
import { useRunPolling } from "./useRunPolling";
import type { Run } from "../types/run";
vi.mock("../lib/api", () => ({
  api: { run: vi.fn(), steps: vi.fn() },
  ApiError: class extends Error {
    constructor(
      public status: number,
      message: string,
    ) {
      super(message);
    }
  },
}));
const base: Run = {
  run_id: "id",
  status: "RUNNING",
  execution_mode: "MOCK",
  max_steps: 5,
  steps_used: 1,
  created_at: "2026-10-15T00:00:00Z",
  source_ids: [],
};
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.steps).mockResolvedValue([]);
});
afterEach(() => vi.useRealTimers());
test("continues nonterminal polling then stops on terminal", async () => {
  vi.useFakeTimers();
  vi.mocked(api.run)
    .mockResolvedValueOnce(base)
    .mockResolvedValueOnce({ ...base, status: "SUCCEEDED" });
  const { result } = renderHook(() => useRunPolling("id"));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(0);
  });
  expect(result.current.run?.status).toBe("RUNNING");
  await act(async () => {
    await vi.advanceTimersByTimeAsync(2000);
  });
  expect(result.current.run?.status).toBe("SUCCEEDED");
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10000);
  });
  expect(api.run).toHaveBeenCalledTimes(2);
});
test("network error pauses until explicit reconnect", async () => {
  vi.mocked(api.run)
    .mockRejectedValueOnce(new Error("Offline"))
    .mockResolvedValueOnce({ ...base, status: "SUCCEEDED" });
  const { result } = renderHook(() => useRunPolling("id"));
  await waitFor(() => expect(result.current.error).toBe("Offline"));
  expect(api.run).toHaveBeenCalledOnce();
  act(() => result.current.reconnect());
  await waitFor(() => expect(result.current.run?.status).toBe("SUCCEEDED"));
});
test("unmount aborts inflight reads", async () => {
  vi.mocked(api.run).mockImplementation(() => new Promise(() => {}));
  const { unmount } = renderHook(() => useRunPolling("id"));
  const signal = vi.mocked(api.run).mock.calls[0][1];
  unmount();
  expect(signal.aborted).toBe(true);
});
test("401 requests sign-in", async () => {
  vi.mocked(api.run).mockRejectedValue(new ApiError(401, "Sign in"));
  const { result } = renderHook(() => useRunPolling("id"));
  await waitFor(() => expect(result.current.unauthorized).toBe(true));
});
