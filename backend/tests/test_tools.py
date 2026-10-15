import pytest
from app.tools import calculator, knowledge_search, safe_text


@pytest.mark.parametrize("expression,result", [("15 * 60 * 8", "7200"), ("(120 * 30) / 4", "900"), ("-2 + 5 % 2", "-1"), ("1.5 * 2", "3")])
def test_arithmetic(expression, result):
    assert calculator({"expression": expression}).observation.endswith("= " + result)


@pytest.mark.parametrize("expression", ["__import__('os')", "2 ** 1000", "True + 1", "1 / 0", "[1][0]", "1e99", "x + 1", "+" * 201])
def test_rejects_unsafe_and_unbounded(expression):
    with pytest.raises((ValueError, SyntaxError, ZeroDivisionError)):
        calculator({"expression": expression})


def test_knowledge_returns_stable_ids():
    result = knowledge_search({"query": "SQS EventBridge"})
    assert {"AWS-SQS", "AWS-EVENTBRIDGE"} <= set(result.source_ids)
    assert knowledge_search({"query": "zzzznoresult"}).source_ids == []


def test_redaction():
    text = safe_text("Bearer private.jwt.here password=hunter2 api_key=abcdef AKIA1234567890123456")
    for secret in ["private.jwt.here", "hunter2", "abcdef", "AKIA1234567890123456"]:
        assert secret not in text


def test_json_secret_redaction():
    assert "secret-value" not in safe_text('{"password": "secret-value"}')
