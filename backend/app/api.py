import json
import os

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from mangum import Mangum

from .agent import run_agent
from .auth import get_owner
from .db import MemoryRepository
from .mock_model import FakeModel
from .models import CreateRun, Run, now


def create_app(repo=None, enqueue=None, demo=None):
    demo = os.getenv("DEMO_MODE", "false").lower() == "true" if demo is None else demo
    cloud = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
    if cloud and demo:
        raise RuntimeError("DEMO_MODE is forbidden in Lambda")
    app = FastAPI(title="ReAct Agent Workbench")
    app.state.demo = demo
    if repo is None:
        if demo:
            repo = MemoryRepository()
        elif os.getenv("TABLE_NAME"):
            from .dynamo import DynamoRepository

            repo = DynamoRepository(os.environ["TABLE_NAME"])
        else:
            raise RuntimeError("Enable explicit DEMO_MODE locally or configure TABLE_NAME")
    app.state.repo = repo
    if not demo and enqueue is None:
        import boto3

        sqs = boto3.client("sqs")

        def enqueue(run_id):
            sqs.send_message(QueueUrl=os.environ["QUEUE_URL"], MessageBody=json.dumps({"run_id": run_id}))

    @app.get("/health")
    def health():
        return {"status": "ok", "demo_mode": demo}

    @app.post("/runs", status_code=202)
    def create(payload: CreateRun, background: BackgroundTasks, owner: str = Depends(get_owner)):
        run = Run(task=payload.task, max_steps=payload.max_steps, owner_id=owner)
        repo.create(run)
        try:
            if demo:
                background.add_task(run_agent, repo, run.run_id, FakeModel())
            else:
                enqueue(run.run_id)
        except Exception:
            run.status, run.termination_reason, run.completed_at = "FAILED", "MODEL_ERROR", now()
            run.final_answer = "Could not enqueue the run. Retry submission."
            repo.save(run)
            raise HTTPException(status_code=503, detail={"message": "Could not enqueue run", "run_id": run.run_id}) from None
        return {"run_id": run.run_id, "status": "QUEUED"}

    def owned(run_id, owner):
        run = repo.get(run_id)
        if run is None or run.owner_id != owner:
            raise HTTPException(status_code=404, detail="Run not found")
        return run

    @app.get("/runs/{run_id}")
    def get(run_id: str, owner: str = Depends(get_owner)):
        return owned(run_id, owner).public()

    @app.get("/runs/{run_id}/steps")
    def steps(run_id: str, owner: str = Depends(get_owner)):
        owned(run_id, owner)
        return repo.steps(run_id)

    return app


# Factory keeps imports free of AWS calls for tests and packaging checks.
def handler(event, context):
    global _adapter
    if _adapter is None:
        _adapter = Mangum(create_app(), lifespan="off")
    return _adapter(event, context)


_adapter = None
