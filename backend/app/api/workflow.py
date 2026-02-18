"""
Workflow CRUD API endpoints
"""

import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.workflow import (
    GraphData,
    Workflow,
    WorkflowCreate,
    WorkflowList,
    WorkflowUpdate,
    parse_workflow_nodes,
)
from app.models.workflow_db import WorkflowDB
from app.core.audit import audit_log
from app.core.auth import User, get_current_user
from app.middleware.rate_limit import limiter
from app.utils.sse import format_sse_event, with_heartbeat

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

EXPORT_VERSION = 1


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


def _row_to_workflow_model(row: WorkflowDB) -> Workflow:
    graph_data = json.loads(row.graph_data_json) if row.graph_data_json else {}
    created_at = ensure_utc_datetime(row.created_at)
    updated_at = ensure_utc_datetime(row.updated_at)

    return Workflow(
        id=row.id,
        name=row.name,
        description=row.description,
        graph_data=GraphData(**graph_data) if graph_data else GraphData(),
        created_at=created_at,
        updated_at=updated_at,
    )


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


async def _get_workflow_row_by_id(workflow_id: str) -> WorkflowDB:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WorkflowDB).where(WorkflowDB.id == workflow_id)
        )
        row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    return row


def _validate_graph_data_or_422(graph_data: GraphData) -> None:
    try:
        parse_workflow_nodes(graph_data.nodes)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


async def _get_workflow_by_id(workflow_id: str) -> Workflow:
    row = await _get_workflow_row_by_id(workflow_id)
    return _row_to_workflow_model(row)


async def get_workflow_for_internal(workflow_id: str) -> Workflow:
    return await _get_workflow_by_id(workflow_id)


@router.get("/{workflow_id}/export", response_model=WorkflowExportPayload)
async def export_workflow(
    workflow_id: str, user: User = Depends(get_current_user)
) -> WorkflowExportPayload:
    workflow = await _get_workflow_by_id(workflow_id)
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

    async with AsyncSessionLocal() as db:
        db.add(
            WorkflowDB(
                id=workflow_id,
                user_id=str(user.id),
                name=payload.workflow.name,
                description=payload.workflow.description,
                graph_data_json=json.dumps(
                    payload.workflow.graph_data.model_dump(), ensure_ascii=False
                ),
                template_name=template_name,
                created_at=now,
                updated_at=now,
            )
        )
        await db.commit()

    audit_log(
        request=request,
        user_id=user.id,
        action="template_import" if template_name else "workflow_import",
        resource_id=workflow_id,
        extra={"template_name": template_name} if template_name else None,
    )

    row = await _get_workflow_row_by_id(workflow_id)
    return _row_to_workflow_model(row)


@router.get("", response_model=WorkflowList)
async def list_workflows(user: User = Depends(get_current_user)) -> WorkflowList:
    """List all workflows"""
    _ = user
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(WorkflowDB))
        rows = result.scalars().all()

    workflows = [_row_to_workflow_model(row) for row in rows]
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

    async with AsyncSessionLocal() as db:
        db.add(
            WorkflowDB(
                id=workflow_id,
                user_id=str(user.id),
                name=workflow_data.name,
                description=workflow_data.description,
                graph_data_json=json.dumps(
                    workflow_data.graph_data.model_dump(), ensure_ascii=False
                ),
                created_at=now,
                updated_at=now,
            )
        )
        await db.commit()

    audit_log(
        request=request,
        user_id=user.id,
        action="workflow_create",
        resource_id=workflow_id,
    )

    row = await _get_workflow_row_by_id(workflow_id)
    return _row_to_workflow_model(row)


@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(
    workflow_id: str, user: User = Depends(get_current_user)
) -> Workflow:
    """Get a workflow by ID"""
    _ = user
    row = await _get_workflow_row_by_id(workflow_id)
    return _row_to_workflow_model(row)


@router.put("/{workflow_id}", response_model=Workflow)
async def update_workflow(
    workflow_id: str,
    update_data: WorkflowUpdate,
    user: User = Depends(get_current_user),
) -> Workflow:
    """Update an existing workflow"""
    if update_data.graph_data is not None:
        _validate_graph_data_or_422(update_data.graph_data)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WorkflowDB).where(WorkflowDB.id == workflow_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(
                status_code=404, detail=f"Workflow {workflow_id} not found"
            )

        if update_data.name is not None:
            row.name = update_data.name
        if update_data.description is not None:
            row.description = update_data.description
        if update_data.graph_data is not None:
            row.graph_data_json = json.dumps(
                update_data.graph_data.model_dump(), ensure_ascii=False
            )
        row.updated_at = datetime.now(timezone.utc)
        await db.commit()

    refreshed = await _get_workflow_row_by_id(workflow_id)
    return _row_to_workflow_model(refreshed)


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    request: Request,
    workflow_id: str,
    user: User = Depends(get_current_user),
) -> None:
    """Delete a workflow"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WorkflowDB).where(WorkflowDB.id == workflow_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(
                status_code=404, detail=f"Workflow {workflow_id} not found"
            )
        await db.delete(row)
        await db.commit()

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
    row = await _get_workflow_row_by_id(workflow_id)
    template_name_obj = row.template_name
    template_name = (
        template_name_obj.strip()[:200] if isinstance(template_name_obj, str) else None
    )
    if template_name == "":
        template_name = None

    workflow = _row_to_workflow_model(row)
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
        with_heartbeat(generate()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
