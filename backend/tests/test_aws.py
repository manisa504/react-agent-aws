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
    boto3.client("dynamodb", region_name="us-east-1").create_table(
        TableName="runs",
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}, {"AttributeName": "SK", "KeyType": "RANGE"}],
        AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}, {"AttributeName": "SK", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    repo = DynamoRepository("runs", "us-east-1")
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
