"""Exercise the running local API through Vite's proxy, without AWS."""

import time

import httpx


def main():
    base = "http://127.0.0.1:5173"
    with httpx.Client(base_url=base, timeout=10) as client:
        for path in ["/", "/app", "/api/health"]:
            assert client.get(path).status_code == 200, path
        for task, expected in [
            ("SQS and EventBridge. Calculate: 15 * 60 * 8", "SUCCEEDED"),
            ("[loop]", "LIMIT_REACHED"),
            ("[invalid]", "FAILED"),
            ("[error]", "FAILED"),
            ("[unsupported]", "FAILED"),
        ]:
            response = client.post("/api/runs", json={"task": task, "max_steps": 5})
            assert response.status_code == 202
            run_id = response.json()["run_id"]
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                run = client.get(f"/api/runs/{run_id}").json()
                if run["status"] in {"SUCCEEDED", "LIMIT_REACHED", "FAILED"}:
                    break
                time.sleep(0.1)
            assert run["status"] == expected, run
            steps = client.get(f"/api/runs/{run_id}/steps").json()
            assert [s["step_number"] for s in steps] == list(range(1, len(steps) + 1))
            assert run["execution_mode"] == "MOCK" and run["token_usage"] is None
            if expected == "SUCCEEDED":
                assert "7200" in run["final_answer"]
            print(f"PASS {task[:30]} -> {run['status']} / {run['termination_reason']}")
        assert client.post("/api/runs", json={"task": "x" * 2001}).status_code == 422
    print("PASS landing, /app refresh, proxy, validation and five local scenarios")


if __name__ == "__main__":
    main()
