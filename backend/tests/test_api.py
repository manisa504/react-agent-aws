from fastapi.testclient import TestClient
import pytest
from app.api import create_app
from app.auth import get_owner
from app.db import MemoryRepository


def test_local_api_no_aws(monkeypatch):
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    client = TestClient(create_app(demo=True))
    assert client.get("/health").json()["demo_mode"]
    response = client.post("/runs", json={"task": "SQS and EventBridge", "max_steps": 5})
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    run = client.get("/runs/" + run_id).json()
    assert run["status"] == "SUCCEEDED"
    assert "owner_id" not in run and "task" not in run
    assert len(client.get(f"/runs/{run_id}/steps").json()) == 3


@pytest.mark.parametrize(
    "payload",
    [
        {"task": ""},
        {"task": "   "},
        {"task": "x" * 2001},
        {"task": "x", "max_steps": 9},
        {"task": "x", "max_steps": 2},
        {"task": "x", "max_steps": "5"},
        {"task": "x", "owner_id": "other"},
    ],
)
def test_validation(payload):
    client = TestClient(create_app(demo=True))
    assert client.post("/runs", json=payload).status_code == 422


def test_cloud_requires_trusted_gateway_claims():
    client = TestClient(create_app(repo=MemoryRepository(), enqueue=lambda _: None, demo=False))
    assert client.get("/health").status_code == 200
    assert client.post("/runs", json={"task": "task"}, headers={"Authorization": "Bearer made-up", "X-Owner": "alice"}).status_code == 401


def test_ownership():
    app = create_app(repo=MemoryRepository(), enqueue=lambda _: None, demo=False)
    app.dependency_overrides[get_owner] = lambda: "alice"
    client = TestClient(app)
    run_id = client.post("/runs", json={"task": "hello"}).json()["run_id"]
    assert client.get("/runs/" + run_id).status_code == 200
    app.dependency_overrides[get_owner] = lambda: "bob"
    assert client.get("/runs/" + run_id).status_code == 404
    assert client.get(f"/runs/{run_id}/steps").status_code == 404


def test_enqueue_failure_is_terminal():
    def fail(_):
        raise RuntimeError("private details")

    repo = MemoryRepository()
    app = create_app(repo=repo, enqueue=fail, demo=False)
    app.dependency_overrides[get_owner] = lambda: "a"
    response = TestClient(app).post("/runs", json={"task": "hello"})
    assert response.status_code == 503
    run = repo.get(response.json()["detail"]["run_id"])
    assert run.status == "FAILED" and run.completed_at
    assert "private" not in response.text


def test_cloud_demo_forbidden(monkeypatch):
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "test")
    with pytest.raises(RuntimeError, match="forbidden"):
        create_app(demo=True)
