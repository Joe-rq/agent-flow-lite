"""
Workflow CRUD API endpoints
"""

import json
import os
import uuid
from collections.abc import AsyncGenerator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from filelock import FileLock
from pydantic import BaseModel, Field, ValidationError

from app.models.workflow import (
    GraphData,
    Workflow,
    WorkflowCreate,
    WorkflowList,
    WorkflowUpdate,
    parse_workflow_nodes,
)
from app.core.audit import audit_log
from app.core.auth import User, get_current_user
from app.middleware.rate_limit import limiter
from app.utils.sse import format_sse_event

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

EXPORT_VERSION = 1

DATA_DIR = Path(__file__).parent.parent.parent / "data"
WORKFLOW_FILE = DATA_DIR / "workflows.json"
_workflow_lock = FileLock(str(WORKFLOW_FILE) + ".lock")


class WorkflowExecuteRequest(BaseModel):
    """Request body for workflow execution."""

    input: str = Field(..., min_length=1, description="Workflow input text")
    model: str | None = Field(
        default=None,
        description="Optional model override. Supports provider:model format.",
    )


class WorkflowExportObject(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None
    graph_data: GraphData


class WorkflowExportPayload(BaseModel):
    version: int
    workflow: WorkflowExportObject


class WorkflowImportPayload(BaseModel):
    version: int
    workflow: WorkflowExportObject


def ensure_utc_datetime(value: datetime) -> datetime:
    """Normalize datetime to UTC-aware for safe comparisons and responses."""
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def ensure_data_dir() -> None:
    """Ensure data directory exists"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _atomic_write_workflow_file(data: dict[str, Any]) -> None:
    ensure_data_dir()
    tmp_path = WORKFLOW_FILE.with_name(WORKFLOW_FILE.name + f".tmp.{uuid.uuid4().hex}")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, WORKFLOW_FILE)
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass


@contextmanager
def locked_workflows():
    """Atomic read-modify-write for workflows.json under a single lock."""
    ensure_data_dir()
    with _workflow_lock:
        if not WORKFLOW_FILE.exists():
            data = {"workflows": {}}
        else:
            try:
                with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = {"workflows": {}}

        yield data

        with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def load_workflows_readonly() -> dict[str, Any]:
    """Read-only load (for GET endpoints that don't write back)."""
    ensure_data_dir()
    with _workflow_lock:
        if not WORKFLOW_FILE.exists():
            return {"workflows": {}}
        try:
            with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"workflows": {}}


def workflow_to_model(workflow_id: str, data: dict[str, Any]) -> Workflow:
    """Convert stored workflow data to Workflow model"""
    graph_data = data.get("graph_data", {})
    if isinstance(graph_data, str):
        graph_data = json.loads(graph_data)

    created_at = ensure_utc_datetime(datetime.fromisoformat(data["created_at"]))
    updated_at = ensure_utc_datetime(datetime.fromisoformat(data["updated_at"]))

    return Workflow(
        id=workflow_id,
        name=data["name"],
        description=data.get("description"),
        graph_data=GraphData(**graph_data) if graph_data else GraphData(),
        created_at=created_at,
        updated_at=updated_at,
    )


def _validate_graph_data_or_422(graph_data: GraphData) -> None:
    try:
        parse_workflow_nodes(graph_data.nodes)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


def _get_workflow_by_id(workflow_id: str) -> Workflow:
    """Internal helper to load a single workflow (no auth dependency)."""
    data = load_workflows_readonly()
    workflows = data.get("workflows", {})
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    return workflow_to_model(workflow_id, workflows[workflow_id])


def _get_stored_workflow_dict(workflow_id: str) -> dict[str, Any]:
    data = load_workflows_readonly()
    workflows = data.get("workflows", {})
    stored = workflows.get(workflow_id)
    if not isinstance(stored, dict):
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    return stored


@router.get("/{workflow_id}/export", response_model=WorkflowExportPayload)
async def export_workflow(
    workflow_id: str, user: User = Depends(get_current_user)
) -> WorkflowExportPayload:
    workflow = _get_workflow_by_id(workflow_id)
    _ = user
    return WorkflowExportPayload(
        version=EXPORT_VERSION,
        workflow=WorkflowExportObject(
            name=workflow.name,
            description=workflow.description,
            graph_data=workflow.graph_data,
        ),
    )


@router.post("/import", response_model=Workflow, status_code=201)
async def import_workflow(
    request: Request,
    payload: WorkflowImportPayload,
    user: User = Depends(get_current_user),
) -> Workflow:
    if payload.version != EXPORT_VERSION:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported workflow export version: {payload.version}",
        )

    _validate_graph_data_or_422(payload.workflow.graph_data)

    raw_template_name_obj = request.headers.get("X-Template-Name")
    template_name: str | None = None
    if isinstance(raw_template_name_obj, str):
        candidate = raw_template_name_obj.strip()
        if candidate:
            template_name = candidate[:200]

    workflow_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    new_workflow = {
        "name": payload.workflow.name,
        "description": payload.workflow.description,
        "graph_data": payload.workflow.graph_data.model_dump(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    if template_name:
        new_workflow["template_name"] = template_name

    ensure_data_dir()
    with _workflow_lock:
        if not WORKFLOW_FILE.exists():
            data: dict[str, Any] = {"workflows": {}}
        else:
            try:
                with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = {"workflows": {}}

        workflows = data.setdefault("workflows", {})
        workflows[workflow_id] = new_workflow

        try:
            _atomic_write_workflow_file(data)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Failed to persist imported workflow",
            ) from exc

    audit_log(
        request=request,
        user_id=user.id,
        action="template_import" if template_name else "workflow_import",
        resource_id=workflow_id,
        extra={"template_name": template_name} if template_name else None,
    )

    return workflow_to_model(workflow_id, new_workflow)


@router.get("", response_model=WorkflowList)
async def list_workflows(user: User = Depends(get_current_user)) -> WorkflowList:
    """List all workflows"""
    data = load_workflows_readonly()
    workflows_data = data.get("workflows", {})

    workflows = [
        workflow_to_model(wf_id, wf_data) for wf_id, wf_data in workflows_data.items()
    ]
    workflows.sort(key=lambda w: w.created_at, reverse=True)

    return WorkflowList(items=workflows, total=len(workflows))


@router.post("", response_model=Workflow, status_code=201)
async def create_workflow(
    request: Request,
    workflow_data: WorkflowCreate,
    user: User = Depends(get_current_user),
) -> Workflow:
    """Create a new workflow"""
    _validate_graph_data_or_422(workflow_data.graph_data)

    workflow_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    new_workflow = {
        "name": workflow_data.name,
        "description": workflow_data.description,
        "graph_data": workflow_data.graph_data.model_dump(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    with locked_workflows() as data:
        workflows = data.setdefault("workflows", {})
        workflows[workflow_id] = new_workflow

    audit_log(
        request=request,
        user_id=user.id,
        action="workflow_create",
        resource_id=workflow_id,
    )

    return workflow_to_model(workflow_id, new_workflow)


@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(
    workflow_id: str, user: User = Depends(get_current_user)
) -> Workflow:
    """Get a workflow by ID"""
    return _get_workflow_by_id(workflow_id)


@router.put("/{workflow_id}", response_model=Workflow)
async def update_workflow(
    workflow_id: str,
    update_data: WorkflowUpdate,
    user: User = Depends(get_current_user),
) -> Workflow:
    """Update an existing workflow"""
    if update_data.graph_data is not None:
        _validate_graph_data_or_422(update_data.graph_data)

    with locked_workflows() as data:
        workflows = data.get("workflows", {})
        if workflow_id not in workflows:
            raise HTTPException(
                status_code=404, detail=f"Workflow {workflow_id} not found"
            )

        existing = workflows[workflow_id]
        if update_data.name is not None:
            existing["name"] = update_data.name
        if update_data.description is not None:
            existing["description"] = update_data.description
        if update_data.graph_data is not None:
            existing["graph_data"] = update_data.graph_data.model_dump()
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()

    return workflow_to_model(workflow_id, existing)


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    request: Request,
    workflow_id: str,
    user: User = Depends(get_current_user),
) -> None:
    """Delete a workflow"""
    with locked_workflows() as data:
        workflows = data.get("workflows", {})
        if workflow_id not in workflows:
            raise HTTPException(
                status_code=404, detail=f"Workflow {workflow_id} not found"
            )
        del workflows[workflow_id]

    audit_log(
        request=request,
        user_id=user.id,
        action="workflow_delete",
        resource_id=workflow_id,
    )


@router.post("/{workflow_id}/execute")
@limiter.limit("10/minute")
async def execute_workflow(
    request: Request,
    workflow_id: str,
    input_data: WorkflowExecuteRequest,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    stored_workflow = _get_stored_workflow_dict(workflow_id)
    template_name_obj = stored_workflow.get("template_name")
    template_name = (
        template_name_obj.strip()[:200] if isinstance(template_name_obj, str) else None
    )
    if template_name == "":
        template_name = None

    workflow = workflow_to_model(workflow_id, stored_workflow)
    _validate_graph_data_or_422(workflow.graph_data)

    audit_log(
        request=request,
        user_id=user.id,
        action="workflow_execute",
        resource_id=workflow_id,
    )

    async def generate() -> AsyncGenerator[str, None]:
        from app.core.workflow.workflow_engine import WorkflowEngine

        engine = WorkflowEngine(workflow)
        template_execute_logged = False
        async for event in engine.execute(
            input_data.input,
            user_id=user.id,
            model=input_data.model,
        ):
            event_type = event.get("type", "unknown")
            if (
                not template_execute_logged
                and event_type == "workflow_complete"
                and template_name
            ):
                audit_log(
                    request=request,
                    user_id=user.id,
                    action="template_execute_success",
                    resource_id=workflow_id,
                    extra={"template_name": template_name},
                )
                template_execute_logged = True
            payload = {k: v for k, v in event.items() if k != "type"}
            yield format_sse_event(event_type, payload)
        yield format_sse_event("done", {"status": "complete"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
