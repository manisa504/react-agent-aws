import re

from .models import FinalAnswer, ToolCall


class FakeModel:
    """Deterministic demonstration adapter, not a language model."""

    usage = None
    invoked = False

    def decide(self, task, history):
        text = task.lower()
        if "[loop]" in text:
            return ToolCall(name="calculator", arguments={"expression": "1 + 1"})
        if "[invalid]" in text:
            return ToolCall(name="shell", arguments={"command": "blocked"})
        if "[error]" in text:
            return ToolCall(name="calculator", arguments={"expression": "1 / 0"})
        if "[badargs]" in text:
            return ToolCall(name="calculator", arguments={"expression": 42})
        if "[unsupported]" in text:
            return FinalAnswer(text="The curated notes do not support this request.", supported=False)
        if "[false-citation]" in text:
            return FinalAnswer(text="Unsupported claim [INVENTED].", source_ids=["INVENTED"])
        if not history:
            return ToolCall(
                name="knowledge_search", arguments={"query": "SQS EventBridge photo processing queue" if "[injection]" not in text else "untrusted content"}
            )
        if len(history) == 1:
            expression = re.search(r"calculate\s*:\s*([\d\s()+*/%.\-]+)", text)
            return ToolCall(name="calculator", arguments={"expression": expression.group(1).strip() if expression else "15 * 60 * 8"})
        ids = history[0].source_ids
        calculation = history[1].observation
        return FinalAnswer(
            text=f"MOCK demonstration: SQS fits buffered work consumed by workers; EventBridge routes events to matching targets. Curated notes are not live documentation. Calculation: {calculation}. "
            + " ".join(f"[{source}]" for source in ids),
            source_ids=ids,
        )
