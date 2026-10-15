from threading import Lock
from typing import Protocol

from .models import Run, StepEvent


class Repository(Protocol):
    def create(self, run: Run) -> None: ...
    def get(self, run_id: str) -> Run | None: ...
    def save(self, run: Run) -> None: ...
    def claim(self, run_id: str) -> Run | None: ...
    def add_step(self, run_id: str, step: StepEvent) -> None: ...
    def steps(self, run_id: str) -> list[StepEvent]: ...


class MemoryRepository:
    def __init__(self):
        self.runs: dict[str, Run] = {}
        self.events: dict[str, list[StepEvent]] = {}
        self.lock = Lock()

    def create(self, run: Run):
        with self.lock:
            self.runs[run.run_id] = run.model_copy(deep=True)
            self.events[run.run_id] = []

    def get(self, run_id: str):
        with self.lock:
            run = self.runs.get(run_id)
            return run.model_copy(deep=True) if run else None

    def save(self, run: Run):
        with self.lock:
            self.runs[run.run_id] = run.model_copy(deep=True)

    def claim(self, run_id: str):
        with self.lock:
            run = self.runs.get(run_id)
            if not run or run.status != "QUEUED":
                return None
            run.status = "RUNNING"
            return run.model_copy(deep=True)

    def add_step(self, run_id: str, step: StepEvent):
        with self.lock:
            self.events[run_id].append(step.model_copy(deep=True))

    def steps(self, run_id: str):
        with self.lock:
            return [step.model_copy(deep=True) for step in self.events.get(run_id, [])]
