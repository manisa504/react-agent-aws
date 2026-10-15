import logging
import re
import time

from .db import Repository
from .models import FinalAnswer, StepEvent, ToolCall, now
from .tools import SCHEMAS, TOOLS, safe_text


def run_agent(repo: Repository, run_id: str, model, budget_seconds: float = 150):
    run = repo.claim(run_id)
    if run is None:
        return
    history = []
    started = time.monotonic()

    def finish(status, reason, answer=None, sources=None):
        run.status, run.termination_reason = status, reason
        run.final_answer = safe_text(answer) if answer else None
        run.source_ids = sources or []
        run.completed_at = now()
        run.token_usage = model.usage
        if getattr(model, "invoked", False):
            run.execution_mode = "BEDROCK"
        repo.save(run)
        logging.getLogger(__name__).warning("run_finished run_id=%s status=%s reason=%s", run_id, status, reason)

    for number in range(1, run.max_steps + 1):
        step = StepEvent(step_number=number, action_summary="Request model action")
        run.steps_used = number
        try:
            if time.monotonic() - started >= budget_seconds:
                raise TimeoutError()
            action = model.decide(run.task, history)
            if getattr(model, "invoked", False):
                run.execution_mode = "BEDROCK"
            if time.monotonic() - started >= budget_seconds:
                raise TimeoutError()
            run.token_usage = model.usage
            if isinstance(action, FinalAnswer):
                actual = {source for event in history for source in event.source_ids}
                inline_ids = set(re.findall(r"\[([A-Z][A-Z0-9_-]*)\]", action.text))
                has_calculation = any(event.tool_name == "calculator" for event in history)
                unsupported = (
                    not action.supported
                    or not history
                    or (not action.source_ids and not has_calculation)
                    or not set(action.source_ids).issubset(actual)
                    or not inline_ids.issubset(set(action.source_ids))
                )
                step.action_summary = "Evidence insufficient" if unsupported else "Final answer validated"
                step.source_ids = [] if unsupported else action.source_ids
                repo.add_step(run_id, step)
                finish(
                    "FAILED" if unsupported else "SUCCEEDED",
                    "UNSUPPORTED" if unsupported else "FINAL_ANSWER",
                    "Insufficient retrieved evidence to support this answer." if unsupported else action.text,
                    step.source_ids,
                )
                return
            if not isinstance(action, ToolCall):
                raise ValueError("Malformed model action")
            if action.name not in TOOLS:
                step.action_summary, step.error = "Tool rejected", "INVALID_TOOL"
                repo.add_step(run_id, step)
                finish("FAILED", "INVALID_TOOL", "The requested tool is not allowed.")
                return
            step.tool_name = action.name
            step.action_summary = f"Execute {action.name}"
            try:
                args = SCHEMAS[action.name].model_validate(action.arguments).model_dump()
                step.tool_input = {key: safe_text(value) for key, value in args.items()}
                result = TOOLS[action.name](args)
            except Exception:
                step.error = "TOOL_ERROR"
                step.observation = "Tool failed or arguments were invalid."
                repo.add_step(run_id, step)
                finish("FAILED", "TOOL_ERROR", "The tool could not complete this request.")
                return
            step.observation = safe_text(result.observation)
            step.source_ids = result.source_ids
            repo.add_step(run_id, step)
            history.append(step)
            repo.save(run)
        except Exception as error:
            reason = "TIMEOUT" if isinstance(error, TimeoutError) else "MODEL_ERROR"
            step.action_summary, step.error = "Execution stopped safely", reason
            repo.add_step(run_id, step)
            finish("FAILED", reason, "Execution stopped. Retry or simplify the task.")
            return
    finish("LIMIT_REACHED", "STEP_LIMIT", "Stopped at the configured step limit. Review the observations or simplify your task.")
