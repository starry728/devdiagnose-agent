import hashlib
import time

import pytest
from devdiagnose.retrieval import retrieve
from devdiagnose.sample import QUESTION, SOURCES


def example_sources():
    return [
        {"id": str(i), "sha256": hashlib.sha256(s["content"].encode()).hexdigest(), **s}
        for i, s in enumerate(SOURCES)
    ]


def test_version_filter_excludes_old_docs():
    found = retrieve(example_sources(), QUESTION)
    assert any(e["path"].endswith("migration-v2.md") for e in found["evidence"])
    assert all(not e["path"].endswith("usage-v1.md") for e in found["evidence"])
    assert found["excluded"][0]["version"] == "1.0.0"


def test_unrelated_question_abstains():
    assert retrieve(example_sources(), "zebra_billing_missing_invoice")["evidence"] == []


def test_end_to_end_report_and_history(client):
    workspace = client.post("/api/workspaces", json={"name": "测试"}).json()["id"]
    demo = client.post(f"/api/workspaces/{workspace}/demo").json()
    assert demo["synthetic"]
    task_id = client.post(f"/api/workspaces/{workspace}/tasks", json={"question": demo["question"]}).json()[
        "id"
    ]
    for _ in range(100):
        task = client.get(f"/api/tasks/{task_id}").json()
        if task["status"] in {"completed", "failed"}:
            break
        time.sleep(0.05)
    assert task["status"] == "completed", task
    assert task["result"]["metrics"]["model_calls"] == 0
    assert task["result"]["excluded"]
    assert any(e["stage"] == "retrieval" for e in task["events"])
    assert "没有调用大模型" in client.get(f"/api/tasks/{task_id}/report").text
    assert client.get(f"/api/workspaces/{workspace}/tasks").json()[0]["id"] == task_id
    assert client.post(f"/api/tasks/{task_id}/resume").status_code == 409


def test_task_uses_fixed_source_snapshot(client):
    from devdiagnose import store
    from devdiagnose.harness import run_local

    workspace = client.post("/api/workspaces", json={"name": "隔离"}).json()["id"]
    client.post(f"/api/workspaces/{workspace}/demo")
    snapshot = store.sources(workspace)
    task_id = client.post(f"/api/workspaces/{workspace}/tasks", json={"question": QUESTION}).json()["id"]
    for _ in range(100):
        task = client.get(f"/api/tasks/{task_id}").json()
        if task["status"] == "completed":
            break
        time.sleep(0.05)
    result = run_local(task, [])  # Completed graph checkpoint holds the original evidence.
    assert result["evidence"] and len(snapshot) == 5


@pytest.mark.parametrize(
    "path", ["../key.py", "C:\\private\\key.py", ".env", ".git/config.txt", ".venv/config.py"]
)
def test_rejects_unsafe_source_paths(client, path):
    w = client.post("/api/workspaces", json={"name": "边界"}).json()["id"]
    assert (
        client.post(f"/api/workspaces/{w}/sources", json={"path": path, "content": "secret"}).status_code
        == 422
    )


def test_unconfigured_model_rejected_without_fallback(client):
    w = client.post("/api/workspaces", json={"name": "模型"}).json()["id"]
    client.post(f"/api/workspaces/{w}/demo")
    assert (
        client.post(f"/api/workspaces/{w}/tasks", json={"question": QUESTION, "mode": "model"}).status_code
        == 409
    )


def test_upload_and_workspace_isolation(client):
    w = client.post("/api/workspaces", json={"name": "上传"}).json()["id"]
    assert (
        client.post(
            f"/api/workspaces/{w}/upload", files={"files": ("test.py", b"raise RuntimeError('demo')")}
        ).status_code
        == 201
    )
    assert len(client.get(f"/api/workspaces/{w}/sources").json()) == 1
    other = client.post("/api/workspaces", json={"name": "空"}).json()["id"]
    assert client.get(f"/api/workspaces/{other}/sources").json() == []
    assert (
        client.post(f"/api/workspaces/{w}/upload", files={"files": ("big.txt", b"x" * 200_001)}).status_code
        == 400
    )
