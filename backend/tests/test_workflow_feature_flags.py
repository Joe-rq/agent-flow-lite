from datetime import datetime, timezone

import httpx
import pytest

from app.core.workflow.workflow_engine import WorkflowEngine
from app.models.workflow import GraphData, Workflow
from app.utils.code_sandbox import SandboxResult


def _build_workflow(graph_data: GraphData) -> Workflow:
    now = datetime.now(timezone.utc)
    return Workflow(
        id="wf-feature-flag",
        name="Feature Flag Workflow",
        description=None,
        graph_data=graph_data,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_code_node_disabled_by_feature_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _disabled(flag_key: str) -> bool:
        del flag_key
        return False

    monkeypatch.setattr(
        "app.core.workflow.workflow_nodes.is_feature_enabled", _disabled
    )

    workflow = _build_workflow(
        GraphData(
            nodes=[
                {"id": "start-1", "type": "start", "data": {}},
                {"id": "code-1", "type": "code", "data": {"code": "print('ok')"}},
                {"id": "end-1", "type": "end", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "start-1", "target": "code-1"},
                {"id": "e2", "source": "code-1", "target": "end-1"},
            ],
        )
    )

    events = [event async for event in WorkflowEngine(workflow).execute("payload")]
    assert any(
        event.get("type") == "workflow_error"
        and "管理员禁用" in str(event.get("error", ""))
        for event in events
    )


@pytest.mark.asyncio
async def test_code_node_executes_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _enabled(flag_key: str) -> bool:
        del flag_key
        return True

    def _fake_execute_python(*args, **kwargs) -> SandboxResult:
        del args, kwargs
        return SandboxResult(ok=True, stdout="sandbox-ok", stderr="", error="")

    monkeypatch.setattr("app.core.workflow.workflow_nodes.is_feature_enabled", _enabled)
    monkeypatch.setattr(
        "app.core.workflow.workflow_nodes.execute_python",
        _fake_execute_python,
    )

    workflow = _build_workflow(
        GraphData(
            nodes=[
                {"id": "start-1", "type": "start", "data": {}},
                {"id": "code-1", "type": "code", "data": {"code": "print('ok')"}},
                {"id": "end-1", "type": "end", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "start-1", "target": "code-1"},
                {"id": "e2", "source": "code-1", "target": "end-1"},
            ],
        )
    )

    events = [event async for event in WorkflowEngine(workflow).execute("payload")]
    assert events[-1]["type"] == "workflow_complete"
    assert events[-1]["final_output"] == "sandbox-ok"


@pytest.mark.asyncio
async def test_http_node_executes_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _enabled(flag_key: str) -> bool:
        del flag_key
        return True

    async def _fake_request(self, *args, **kwargs):
        del self, args, kwargs
        req = httpx.Request("GET", "https://example.com")
        return httpx.Response(status_code=200, request=req, text="pong")

    monkeypatch.setattr("app.core.workflow.workflow_nodes.is_feature_enabled", _enabled)
    monkeypatch.setattr(
        "app.core.workflow.workflow_nodes.ensure_url_safe",
        lambda url, allow_domains=None: url,
    )
    monkeypatch.setattr(httpx.AsyncClient, "request", _fake_request)

    workflow = _build_workflow(
        GraphData(
            nodes=[
                {"id": "start-1", "type": "start", "data": {}},
                {
                    "id": "http-1",
                    "type": "http",
                    "data": {"method": "GET", "url": "https://example.com"},
                },
                {"id": "end-1", "type": "end", "data": {}},
            ],
            edges=[
                {"id": "e1", "source": "start-1", "target": "http-1"},
                {"id": "e2", "source": "http-1", "target": "end-1"},
            ],
        )
    )

    events = [event async for event in WorkflowEngine(workflow).execute("payload")]
    assert events[-1]["type"] == "workflow_complete"
    assert events[-1]["final_output"] == "pong"
