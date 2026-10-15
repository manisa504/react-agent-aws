from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

RunStatus = Literal["QUEUED", "RUNNING", "SUCCEEDED", "LIMIT_REACHED", "FAILED"]
TerminationReason = Literal["FINAL_ANSWER", "STEP_LIMIT", "UNSUPPORTED", "MODEL_ERROR", "TOOL_ERROR", "TIMEOUT", "INVALID_TOOL"]
ExecutionMode = Literal["MOCK", "BEDROCK"]
TERMINAL = {"SUCCEEDED", "LIMIT_REACHED", "FAILED"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateRun(StrictModel):
    task: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    max_steps: int = Field(default=5, ge=3, le=8, strict=True)


class TokenUsage(StrictModel):
    input: int = 0
    output: int = 0


class Run(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    task: str
    owner_id: str
    status: RunStatus = "QUEUED"
    execution_mode: ExecutionMode = "MOCK"
    max_steps: int = 5
    steps_used: int = 0
    token_usage: TokenUsage | None = None
    termination_reason: TerminationReason | None = None
    final_answer: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now)
    completed_at: str | None = None

    def public(self) -> dict:
        return self.model_dump(exclude={"owner_id", "task"})


class StepEvent(StrictModel):
    step_number: int
    timestamp: str = Field(default_factory=now)
    action_summary: str
    tool_name: Literal["calculator", "knowledge_search"] | None = None
    tool_input: dict | None = None
    observation: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    error: str | None = None


class ToolCall(StrictModel):
    kind: Literal["tool"] = "tool"
    name: str
    arguments: dict


class FinalAnswer(StrictModel):
    kind: Literal["final"] = "final"
    text: str = Field(min_length=1, max_length=6000)
    source_ids: list[str] = Field(default_factory=list, max_length=10)
    supported: bool = True


class CalculatorArgs(StrictModel):
    expression: str = Field(min_length=1, max_length=200)


class SearchArgs(StrictModel):
    query: str = Field(min_length=1, max_length=300)


class ToolResult(StrictModel):
    observation: str
    source_ids: list[str] = Field(default_factory=list)
