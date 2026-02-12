import json
from unittest.mock import patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from main import create_app


@pytest.fixture(scope='function')
async def client() -> AsyncClient:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac


def build_skill_content(skill_name: str) -> str:
    return f"""---
name: {skill_name}
description: workflow roundtrip skill
inputs:
  - name: text
    required: true
---

请基于输入给出风险判断：{{{{text}}}}"""


def build_workflow_graph(skill_name: str) -> dict:
    return {
        'nodes': [
            {'id': 'start-1', 'type': 'start', 'data': {}},
            {
                'id': 'skill-1',
                'type': 'skill',
                'data': {'skillName': skill_name, 'inputMappings': {'text': 'start-1'}},
            },
            {'id': 'end-1', 'type': 'end', 'data': {}},
        ],
        'edges': [
            {'id': 'e-start-skill', 'source': 'start-1', 'target': 'skill-1'},
            {'id': 'e-skill-end', 'source': 'skill-1', 'target': 'end-1'},
        ],
    }


def parse_sse_events(stream_text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for chunk in stream_text.split('\n\n'):
        if not chunk.strip():
            continue

        event_name = 'message'
        event_data: dict = {}
        for line in chunk.splitlines():
            if line.startswith('event: '):
                event_name = line[len('event: ') :].strip()
            elif line.startswith('data: '):
                payload = line[len('data: ') :]
                event_data = json.loads(payload) if payload else {}

        events.append((event_name, event_data))

    return events


@pytest.mark.asyncio
async def test_skill_create_and_execute_in_workflow_roundtrip(client: AsyncClient) -> None:
    login_resp = await client.post('/api/v1/auth/login', json={'email': f'rt-{uuid4().hex[:8]}@example.com'})
    assert login_resp.status_code == 200
    token = login_resp.json()['token']
    headers = {'Authorization': f'Bearer {token}'}

    skill_name = f'roundtrip-{uuid4().hex[:8]}'
    workflow_id = ''

    try:
        create_skill_resp = await client.post(
            '/api/v1/skills',
            json={'name': skill_name, 'content': build_skill_content(skill_name)},
            headers=headers,
        )
        assert create_skill_resp.status_code == 201

        create_workflow_resp = await client.post(
            '/api/v1/workflows',
            json={
                'name': f'wf-{skill_name}',
                'description': 'skill workflow roundtrip',
                'graph_data': build_workflow_graph(skill_name),
            },
            headers=headers,
        )
        assert create_workflow_resp.status_code == 201
        workflow_id = create_workflow_resp.json()['id']

        async def fake_chat_completion_stream(messages, temperature=0.7):
            del messages, temperature
            yield '风险'
            yield '可控'

        with patch(
            'app.core.skill.skill_executor.chat_completion_stream',
            side_effect=fake_chat_completion_stream,
        ):
            execute_resp = await client.post(
                f'/api/v1/workflows/{workflow_id}/execute',
                json={'input': '供应链延迟两周'},
                headers=headers,
            )

        assert execute_resp.status_code == 200
        assert execute_resp.headers['content-type'].startswith('text/event-stream')

        events = parse_sse_events(execute_resp.text)
        event_names = [event_name for event_name, _ in events]
        assert 'node_error' not in event_names
        assert 'workflow_error' not in event_names

        output = ''.join(payload.get('content', '') for event_name, payload in events if event_name == 'token')
        assert output == '风险可控'

        done_events = [payload for event_name, payload in events if event_name == 'done']
        assert done_events
        assert done_events[-1].get('status') == 'complete'
    finally:
        if workflow_id:
            await client.delete(f'/api/v1/workflows/{workflow_id}', headers=headers)
        await client.delete(f'/api/v1/skills/{skill_name}', headers=headers)
