from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from starlette.requests import Request

import app.api.skill as skill_api
from app.core.skill.skill_loader import SkillValidationError
from app.models.skill import SkillDetail, SkillRunRequest
from app.models.user import User


def _fake_request() -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/skills/demo/run",
        "headers": [],
        "query_string": b"",
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
    }
    return Request(scope)


def _sample_skill() -> SkillDetail:
    now = datetime.now(timezone.utc)
    return SkillDetail(
        name="demo",
        description="demo skill",
        prompt="say {{text}}",
        raw_content="---\nname: demo\n---\n\nsay {{text}}",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_run_skill_returns_streaming_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Executor:
        async def execute(self, skill, inputs, user_id=None):
            _ = (skill, inputs, user_id)
            yield skill_api.format_sse_event("token", {"content": "ok"})
            yield skill_api.format_sse_event("done", {"status": "success"})

    monkeypatch.setattr(
        skill_api.skill_loader, "get_skill", lambda _name: _sample_skill()
    )
    monkeypatch.setattr(skill_api, "get_skill_executor", lambda: _Executor())

    resp = await skill_api.run_skill(
        request=_fake_request(),
        name="demo",
        data=SkillRunRequest(inputs={"text": "hi"}),
        user=User(id=1, email="u@example.com"),
    )

    assert resp.media_type == "text/event-stream"


@pytest.mark.asyncio
async def test_run_skill_maps_missing_skill_to_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_missing(_name: str):
        raise SkillValidationError("skill not found")

    monkeypatch.setattr(skill_api.skill_loader, "get_skill", _raise_missing)

    with pytest.raises(HTTPException) as exc:
        await skill_api.run_skill(
            request=_fake_request(),
            name="missing",
            data=SkillRunRequest(inputs={}),
            user=User(id=1, email="u@example.com"),
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_execute_skill_stream_yields_error_done_on_executor_failure() -> None:
    class _BrokenExecutor(skill_api.SkillExecutor):
        async def execute(self, skill, inputs, user_id=None):
            _ = (skill, inputs, user_id)
            if False:
                yield ""
            raise RuntimeError("boom")

    chunks = [
        c
        async for c in skill_api._execute_skill_stream(
            _sample_skill(),
            {"text": "x"},
            _BrokenExecutor(),
            user_id=1,
        )
    ]

    assert len(chunks) == 1
    assert "event: done" in chunks[0]
    assert '"status": "error"' in chunks[0]
