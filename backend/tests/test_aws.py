import json
from unittest.mock import Mock

import boto3
import pytest
from moto import mock_aws
from app.bedrock_client import BedrockModel
from app.dynamo import DynamoRepository
from app.models import Run, StepEvent


@mock_aws
def test_dynamo_claim_steps_usage_and_ttl():
    boto3.client("dynamodb", region_name="us-east-2").create_table(
        TableName="runs",
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}, {"AttributeName": "SK", "KeyType": "RANGE"}],
        AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}, {"AttributeName": "SK", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    repo = DynamoRepository("runs", "us-east-2")
    run = Run(task="hello", owner_id="alice")
    repo.create(run)
    assert repo.get(run.run_id).owner_id == "alice"
    assert repo.claim(run.run_id).status == "RUNNING"
    assert repo.claim(run.run_id) is None
    repo.add_step(run.run_id, StepEvent(step_number=2, action_summary="Final"))
    repo.add_step(run.run_id, StepEvent(step_number=1, action_summary="Tool"))
    assert [s.step_number for s in repo.steps(run.run_id)] == [1, 2]
    run = repo.get(run.run_id)
    run.status = "SUCCEEDED"
    repo.save(run)
    assert repo.get(run.run_id).status == "SUCCEEDED"
    assert repo.table.get_item(Key=repo.key(run.run_id))["Item"]["ttl"] > 0


def test_bedrock_tools_and_final_usage():
    client = Mock()
    client.converse.side_effect = [
        {
            "stopReason": "tool_use",
            "usage": {"inputTokens": 12, "outputTokens": 6},
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"reasoningContent": {"text": "PRIVATE"}},
                        {"toolUse": {"toolUseId": "t1", "name": "calculator", "input": {"expression": "1+1"}}},
                    ],
                }
            },
        },
        {
            "stopReason": "end_turn",
            "usage": {"inputTokens": 16, "outputTokens": 10},
            "output": {
                "message": {"role": "assistant", "content": [{"text": json.dumps({"kind": "final", "text": "2", "source_ids": [], "supported": True})}]}
            },
        },
    ]
    model = BedrockModel("configured-model", client)
    assert model.decide("task", []).name == "calculator"
    answer = model.decide("task", [StepEvent(step_number=1, action_summary="Tool", observation="2")])
    assert answer.text == "2"
    assert model.usage.input == 28 and model.usage.output == 16 and model.invoked
    request = client.converse.call_args.kwargs
    assert request["inferenceConfig"]["maxTokens"] == 1000
    assert "PRIVATE" not in str(model.messages)
    assert request["messages"][-1]["content"][0]["toolResult"]["toolUseId"] == "t1"


@pytest.mark.parametrize(
    "response",
    [
        {"stopReason": "max_tokens", "output": {"message": {"content": [{"text": "truncated"}]}}},
        {"stopReason": "end_turn", "output": {"message": {"content": [{"text": "not json"}]}}},
    ],
)
def test_bad_model_response(response):
    client = Mock()
    client.converse.return_value = response
    with pytest.raises(ValueError):
        BedrockModel("model", client).decide("task", [])


def test_nova_wire_schema_preserves_server_side_validation():
    from pydantic import ValidationError
    from app.bedrock_client import tool_schema
    from app.models import CalculatorArgs

    schema = tool_schema(CalculatorArgs)
    assert set(schema) == {"type", "properties", "required"}
    assert schema["properties"] == {"expression": {"type": "string"}}
    assert schema["required"] == ["expression"]
    with pytest.raises(ValidationError):
        CalculatorArgs(expression="1" * 201)


def test_structured_completion_validates_without_executing_a_tool():
    client = Mock()
    client.converse.return_value = {
        "stopReason": "tool_use",
        "usage": {"inputTokens": 40, "outputTokens": 20},
        "output": {
            "message": {
                "content": [
                    {"reasoningContent": {"text": "PRIVATE"}},
                    {
                        "toolUse": {
                            "toolUseId": "done",
                            "name": "final_answer",
                            "input": {
                                "text": "Use SQS [AWS-SQS].",
                                "source_ids": ["AWS-SQS"],
                                "supported": True,
                            },
                        }
                    },
                ]
            }
        },
    }
    model = BedrockModel("model", client)
    answer = model.decide("task", [])
    assert answer.kind == "final" and answer.source_ids == ["AWS-SQS"]
    assert model.pending_id is None and model.usage.input == 40
    assert "PRIVATE" not in str(model.messages)
    specs = client.converse.call_args.kwargs["toolConfig"]["tools"]
    assert specs[-1]["toolSpec"]["inputSchema"]["json"]["required"] == ["text", "source_ids", "supported"]
    from app.tools import TOOLS

    assert set(TOOLS) == {"calculator", "knowledge_search"}
    client.converse.return_value["output"]["message"]["content"][-1]["toolUse"]["input"]["unexpected"] = "field"
    with pytest.raises(ValueError):
        BedrockModel("model", client).decide("task", [])


def test_batched_actions_are_serialized_with_one_execution_per_step():
    client = Mock()
    client.converse.side_effect = [
        {
            "stopReason": "tool_use",
            "output": {"message": {"content": [{"toolUse": {"toolUseId": str(i), "name": "calculator", "input": {"expression": str(i)}}} for i in range(2)]}},
        },
        {"stopReason": "end_turn", "output": {"message": {"content": [{"text": json.dumps({"text": "1", "source_ids": []})}]}}},
    ]
    model = BedrockModel("model", client)
    assert model.decide("task", []).arguments == {"expression": "0"}
    history = [StepEvent(step_number=1, action_summary="Tool", observation="0")]
    assert model.decide("task", history).arguments == {"expression": "1"}
    assert client.converse.call_count == 1
    history.append(StepEvent(step_number=2, action_summary="Tool", observation="1"))
    assert model.decide("task", history).kind == "final"
    results = client.converse.call_args.kwargs["messages"][-1]["content"][:2]
    assert [r["toolResult"]["toolUseId"] for r in results] == ["0", "1"]


def test_completion_cannot_bypass_pending_tools_in_same_batch():
    client = Mock()
    client.converse.return_value = {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "content": [
                    {"toolUse": {"toolUseId": "a", "name": "calculator", "input": {"expression": "1"}}},
                    {"toolUse": {"toolUseId": "b", "name": "final_answer", "input": {"text": "1"}}},
                ]
            }
        },
    }
    with pytest.raises(ValueError, match="Completion mixed"):
        BedrockModel("model", client).decide("task", [])


def test_batched_model_requests_cannot_exceed_controller_budget():
    from app.agent import run_agent
    from app.db import MemoryRepository

    repo = MemoryRepository()
    run = Run(task="task", owner_id="owner", max_steps=3)
    repo.create(run)
    client = Mock()
    client.converse.return_value = {
        "stopReason": "tool_use",
        "output": {"message": {"content": [{"toolUse": {"toolUseId": str(i), "name": "calculator", "input": {"expression": str(i)}}} for i in range(5)]}},
    }
    run_agent(repo, run.run_id, BedrockModel("model", client))
    assert repo.get(run.run_id).status == "LIMIT_REACHED"
    assert len(repo.steps(run.run_id)) == 3
    assert client.converse.call_count == 1
