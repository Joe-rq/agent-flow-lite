from __future__ import annotations

import asyncio
import html
import logging
from datetime import datetime, timezone
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.api import workflow as workflow_api
from app.core.audit import audit_log
from app.core.auth import get_current_user
from app.core.feature_flags import is_feature_enabled
from app.core.publish_embed import (
    EmbedTokenExpired,
    EmbedTokenNotFound,
    create_embed_token,
    get_valid_embed_record,
)
from app.core.workflow.workflow_engine import WorkflowEngine
from app.models.user import User
from app.models.workflow import GraphData, Workflow, parse_workflow_nodes
from pydantic import ValidationError


logger = logging.getLogger(__name__)

EXECUTION_TIMEOUT_SECONDS = 30
MAX_INPUT_CHARS = 10_000


async def require_public_embed_enabled() -> None:
    if not await is_feature_enabled("ENABLE_PUBLIC_EMBED"):
        raise HTTPException(status_code=403, detail="Public embed is disabled")


router = APIRouter(
    prefix="/api/v1/publish",
    tags=["publish"],
    dependencies=[Depends(require_public_embed_enabled)],
)


class PublishEmbedRequest(BaseModel):
    workflow_id: str = Field(..., min_length=1)


class PublishEmbedResponse(BaseModel):
    url: str
    token: str
    expires_at: str


async def _execute_workflow_once(*, workflow_id: str, input_text: str) -> str:
    workflow = _get_workflow_by_id(workflow_id)

    engine = WorkflowEngine(workflow)
    final_output = None
    error_message = None

    async with asyncio.timeout(EXECUTION_TIMEOUT_SECONDS):
        async for event in engine.execute(input_text, user_id=None):
            event_obj = cast(dict[str, object], event)
            event_type = event_obj.get("type")
            if event_type == "workflow_error":
                error_message = str(event_obj.get("error") or "Execution failed")
                break
            if event_type == "workflow_complete":
                final_output = event_obj.get("final_output")

    if error_message:
        raise RuntimeError(error_message)

    if final_output is None:
        return ""
    if isinstance(final_output, str):
        return final_output
    return str(final_output)


def _render_page(*, title: str, body_html: str) -> str:
    safe_title = html.escape(title)
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{safe_title}</title>
    <style>
      :root {{ color-scheme: light; }}
      body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; margin: 24px; }}
      .wrap {{ max-width: 920px; margin: 0 auto; }}
      .card {{ border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; background: #fff; }}
      .muted {{ color: #6b7280; font-size: 14px; }}
      input[type=text] {{ width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 10px; }}
      button {{ margin-top: 10px; padding: 10px 12px; border: 1px solid #111827; background: #111827; color: #fff; border-radius: 10px; cursor: pointer; }}
      pre {{ white-space: pre-wrap; word-break: break-word; background: #0b1020; color: #e5e7eb; padding: 12px; border-radius: 10px; }}
      .err {{ border-left: 4px solid #ef4444; padding-left: 12px; }}
    </style>
  </head>
  <body>
    <div class=\"wrap\">
      <div class=\"card\">
        {body_html}
      </div>
      <p class=\"muted\">Generated at {datetime.now(timezone.utc).isoformat()}</p>
    </div>
  </body>
</html>"""


@router.post("/embed", response_model=PublishEmbedResponse)
async def publish_embed(
    request: Request,
    payload: PublishEmbedRequest,
    user: Annotated[User, Depends(get_current_user)],
) -> PublishEmbedResponse:
    workflow = _get_workflow_by_id(payload.workflow_id)
    _validate_graph_data_or_422(workflow.graph_data)

    record = create_embed_token(workflow_id=payload.workflow_id, created_by=user.id)

    url = str(request.base_url).rstrip("/") + f"/api/v1/publish/embed/{record.token}"

    audit_log(
        request=request,
        user_id=user.id,
        action="publish_embed_create",
        resource_id=record.token,
        extra={"workflow_id": payload.workflow_id},
    )

    return PublishEmbedResponse(
        url=url,
        token=record.token,
        expires_at=record.expires_at_iso(),
    )


def _get_workflow_by_id(workflow_id: str) -> Workflow:
    data_obj = cast(object, workflow_api.load_workflows_readonly())
    workflows_map: dict[str, object] = {}
    if isinstance(data_obj, dict):
        raw = cast(dict[object, object], data_obj)
        data_map: dict[str, object] = {
            k: v for k, v in raw.items() if isinstance(k, str)
        }
        workflows_obj = data_map.get("workflows")
        if isinstance(workflows_obj, dict):
            raw_wf = cast(dict[object, object], workflows_obj)
            workflows_map = {k: v for k, v in raw_wf.items() if isinstance(k, str)}

    if workflow_id not in workflows_map:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    stored = workflows_map[workflow_id]
    if not isinstance(stored, dict):
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    stored_raw = cast(dict[object, object], stored)
    stored_map: dict[str, object] = {
        k: v for k, v in stored_raw.items() if isinstance(k, str)
    }
    return workflow_api.workflow_to_model(workflow_id, stored_map)


def _validate_graph_data_or_422(graph_data: GraphData) -> None:
    try:
        _ = parse_workflow_nodes(graph_data.nodes)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


@router.get("/embed/{token}")
async def view_embed(
    request: Request,
    token: str,
    input: str | None = None,
) -> HTMLResponse:
    try:
        record = get_valid_embed_record(token)
    except (EmbedTokenNotFound, EmbedTokenExpired):
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    audit_log(
        request=request,
        user_id=None,
        action="publish_embed_view",
        resource_id=token,
        extra={"workflow_id": record.workflow_id},
    )

    input_value = input or ""
    if len(input_value) > MAX_INPUT_CHARS:
        raise HTTPException(status_code=400, detail="Input too large")

    title = "Workflow Embed"
    form_html = f"""
<h1>Workflow Embed</h1>
<p class=\"muted\">Provide input to execute this workflow once.</p>
<form method=\"get\">
  <label class=\"muted\" for=\"input\">Input</label>
  <input id=\"input\" name=\"input\" type=\"text\" value=\"{html.escape(input_value)}\" />
  <button type=\"submit\">Run</button>
</form>
"""

    if not input_value:
        return HTMLResponse(_render_page(title=title, body_html=form_html))

    try:
        output_text = await _execute_workflow_once(
            workflow_id=record.workflow_id,
            input_text=input_value,
        )
        audit_log(
            request=request,
            user_id=None,
            action="publish_embed_execute",
            resource_id=token,
            extra={"workflow_id": record.workflow_id},
        )
        result_html = (
            form_html + "<h2>Output</h2>" + f"<pre>{html.escape(output_text)}</pre>"
        )
        return HTMLResponse(_render_page(title=title, body_html=result_html))
    except (asyncio.TimeoutError, TimeoutError):
        error_html = form_html + '<p class="err">Execution timed out.</p>'
        return HTMLResponse(_render_page(title=title, body_html=error_html))
    except Exception:
        logger.exception("Public embed execution failed")
        error_html = form_html + '<p class="err">Execution failed.</p>'
        return HTMLResponse(_render_page(title=title, body_html=error_html))
