import ast
import json
import math
import operator
import re
from pathlib import Path

from .models import CalculatorArgs, SearchArgs, ToolResult

KNOWLEDGE = json.loads(Path(__file__).with_name("knowledge.json").read_text())
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Mod: operator.mod}


def calculator(arguments: dict) -> ToolResult:
    expression = CalculatorArgs.model_validate(arguments).expression
    tree = ast.parse(expression, mode="eval")
    if len(list(ast.walk(tree))) > 64:
        raise ValueError("Expression too complex")

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = node.value
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.BinOp) and type(node.op) in OPS:
            value = OPS[type(node.op)](visit(node.left), visit(node.right))
        else:
            raise ValueError("Only numbers, parentheses, + - * / % are allowed")
        if not math.isfinite(value) or abs(value) > 1e12:
            raise ValueError("Result outside supported range")
        return value

    return ToolResult(observation=f"{expression} = {visit(tree):g}")


def knowledge_search(arguments: dict) -> ToolResult:
    query = SearchArgs.model_validate(arguments).query
    words = set(re.findall(r"[a-z0-9]+", query.lower()))
    ranked = sorted(
        KNOWLEDGE,
        key=lambda entry: -(
            5 * len(words & set(re.findall(r"[a-z0-9]+", entry["title"].lower()))) + len(words & set(re.findall(r"[a-z0-9]+", entry["text"].lower())))
        ),
    )
    entries = [entry for entry in ranked if words & set(re.findall(r"[a-z0-9]+", entry["text"].lower() + " " + entry["title"].lower()))][:3]
    return ToolResult(observation=json.dumps(entries), source_ids=[entry["id"] for entry in entries])


TOOLS = {"calculator": calculator, "knowledge_search": knowledge_search}
SCHEMAS = {"calculator": CalculatorArgs, "knowledge_search": SearchArgs}


def safe_text(value: str) -> str:
    value = re.sub(r'(?i)("(?:password|secret|api[_-]?key|token)"\s*:\s*")[^"]*(")', r"\1[REDACTED]\2", value)
    value = re.sub(r"(?i)(bearer\s+)[\w.\-]+", r"\1[REDACTED]", value)
    value = re.sub(r'(?i)((?:password|secret|api[_-]?key|token)\s*[=:]\s*)[^\s,;"}]+', r"\1[REDACTED]", value)
    value = re.sub(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", "[REDACTED]", value)
    return value[:8000]
