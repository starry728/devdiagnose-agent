"""Offline integration test: a scripted model is NOT a real provider evaluation."""

import pytest
from devdiagnose import store
from devdiagnose.harness import run_model
from devdiagnose.sample import QUESTION
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from test_workflow import example_sources


class ScriptedModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


@pytest.mark.parametrize("delegate", [False, True])
def test_deepagents_invokes_search_and_records_evidence(client, monkeypatch, delegate):
    import langchain_openai

    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "search-1",
                    "name": "search_docs",
                    "args": {"query": "SampleClient timeout request_timeout"},
                }
            ],
        ),
        AIMessage(content="候选原因：参数名变化，参考 [E1]。需在独立环境验证，未执行代码。"),
    ]
    if delegate:
        responses = [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "delegate-1",
                        "name": "task",
                        "args": {
                            "subagent_type": "general-purpose",
                            "description": "请查找 SampleClient 2.0 的 timeout 参数迁移证据，返回 E 编号。",
                        },
                    }
                ],
            ),
            *responses,
            AIMessage(content="文档专家查到了参数变化 [E1]，需要实际验证。"),
        ]
    model = ScriptedModel(responses=responses)
    monkeypatch.setattr(langchain_openai, "ChatOpenAI", lambda **kwargs: model)
    monkeypatch.setenv("LLM_API_KEY", "offline-test-placeholder")
    monkeypatch.setenv("LLM_MODEL", "offline-test")
    # The harness writes events against an existing task.
    task_id = store.uid()
    workspace = client.post("/api/workspaces", json={"name": "模型适配测试"}).json()["id"]
    with store.db() as conn:
        conn.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                task_id,
                workspace,
                QUESTION,
                "model",
                "running",
                20,
                "[]",
                None,
                None,
                store.now(),
                store.now(),
            ),
        )
    result = run_model({"id": task_id, "question": QUESTION, "max_steps": 20}, example_sources())
    assert result["evidence"]
    assert result["invalid_citations"] == []
    assert result["metrics"]["model_calls"] == (4 if delegate else 2)
    assert any(e["stage"] == "tool" for e in store.task(task_id)["events"])
