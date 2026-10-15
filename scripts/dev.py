"""Start and cleanly stop the two loopback-only local processes."""

import argparse
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    for port in [8000, 5173]:
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                raise SystemExit(
                    f"Port {port} is occupied. Stop its existing process or reuse the running app."
                )
    env = {
        **os.environ,
        "DEMO_MODE": "true",
        "VITE_DEMO_MODE": "true",
        "VITE_API_URL": "/api",
    }
    if args.preview:
        subprocess.run(
            ["npm", "run", "build"], cwd=ROOT / "frontend", env=env, check=True
        )
    processes = []

    def stop(*_):
        for process in processes:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        processes.append(
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app.api:create_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                ],
                cwd=ROOT / "backend",
                env=env,
                start_new_session=True,
            )
        )
        processes.append(
            subprocess.Popen(
                ["npm", "run", "preview" if args.preview else "dev"],
                cwd=ROOT / "frontend",
                env=env,
                start_new_session=True,
            )
        )
        print(
            "\nLocal MOCK workbench: http://127.0.0.1:5173/app\nIntroduction: http://127.0.0.1:5173/\nAPI: http://127.0.0.1:8000/docs\nCtrl+C stops both processes. Runs are ephemeral.\n",
            flush=True,
        )
        while all(process.poll() is None for process in processes):
            time.sleep(0.25)
        if any(
            process.poll() not in (None, 0, -signal.SIGTERM) for process in processes
        ):
            raise SystemExit("A local service exited unexpectedly.")
    finally:
        stop()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()


if __name__ == "__main__":
    main()
