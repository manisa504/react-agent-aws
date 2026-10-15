import time

import boto3
from boto3.dynamodb.conditions import Attr, Key

from .models import Run, StepEvent


class DynamoRepository:
    def __init__(self, table_name: str, region: str | None = None):
        self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    @staticmethod
    def key(run_id: str) -> dict:
        return {"PK": f"RUN#{run_id}", "SK": "META"}

    def create(self, run: Run):
        self.table.put_item(Item={**self.key(run.run_id), **run.model_dump(), "ttl": int(time.time()) + 604800}, ConditionExpression=Attr("PK").not_exists())

    def get(self, run_id: str):
        item = self.table.get_item(Key=self.key(run_id), ConsistentRead=True).get("Item")
        return Run.model_validate(item) if item else None

    def save(self, run: Run):
        self.table.put_item(Item={**self.key(run.run_id), **run.model_dump(), "ttl": int(time.time()) + 604800})

    def claim(self, run_id: str):
        try:
            self.table.update_item(
                Key=self.key(run_id),
                UpdateExpression="SET #s = :running",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":running": "RUNNING"},
                ConditionExpression=Attr("status").eq("QUEUED"),
            )
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            return None
        return self.get(run_id)

    def add_step(self, run_id: str, step: StepEvent):
        self.table.put_item(
            Item={"PK": f"RUN#{run_id}", "SK": f"STEP#{step.step_number:04d}", **step.model_dump(), "ttl": int(time.time()) + 604800},
            ConditionExpression=Attr("SK").not_exists(),
        )

    def steps(self, run_id: str):
        # At most eight bounded events; well below DynamoDB's 1 MB query page.
        items = self.table.query(KeyConditionExpression=Key("PK").eq(f"RUN#{run_id}") & Key("SK").begins_with("STEP#"), ConsistentRead=True)["Items"]
        return [StepEvent.model_validate({k: v for k, v in item.items() if k not in {"PK", "SK", "ttl"}}) for item in items]
