import json
import os

from .agent import run_agent
from .bedrock_client import BedrockModel
from .dynamo import DynamoRepository


def handler(event, context):
    repo = DynamoRepository(os.environ["TABLE_NAME"])
    failures = []
    for record in event["Records"]:
        try:
            run_id = json.loads(record["body"])["run_id"]
            run_agent(
                repo, run_id, BedrockModel(os.environ["BEDROCK_MODEL_ID"]), budget_seconds=min(150, max(0, context.get_remaining_time_in_millis() / 1000 - 15))
            )
        except Exception:
            # No task content, tokens or exception details in logs.
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}
