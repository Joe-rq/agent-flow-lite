"""
Workflow CRUD API endpoints
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from filelock import FileLock

from app.models.workflow import (
    GraphData,
    Workflow,
    WorkflowCreate,
    WorkflowList,
    WorkflowUpdate,
)

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

DATA_DIR = Path("data")
WORKFLOW_FILE = DATA_DIR / "workflows.json"


def ensure_data_dir() -> None:
    """Ensure data directory exists"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_workflows() -> dict:
    """Load workflows from JSON file"""
    ensure_data_dir()
    lock = FileLock(str(WORKFLOW_FILE) + ".lock")
    with lock:
        if not WORKFLOW_FILE.exists():
            return {"workflows": {}}
        try:
            with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"workflows": {}}


def save_workflows(data: dict) -> None:
    """Save workflows to JSON file"""
    ensure_data_dir()
    lock = FileLock(str(WORKFLOW_FILE) + ".lock")
    with lock:
        with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def workflow_to_model(workflow_id: str, data: dict) -> Workflow:
    """Convert stored workflow data to Workflow model"""
    graph_data = data.get("graph_data", {})
    if isinstance(graph_data, str):
        graph_data = json.loads(graph_data)
    
    return Workflow(
        id=workflow_id,
        name=data["name"],
        description=data.get("description"),
        graph_data=GraphData(**graph_data) if graph_data else GraphData(),
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )


@router.get("", response_model=WorkflowList)
async def list_workflows() -> WorkflowList:
    """
    List all workflows
    
    Returns a list of all stored workflows with pagination metadata.
    """
    data = load_workflows()
    workflows_data = data.get("workflows", {})
    
    workflows = [
        workflow_to_model(wf_id, wf_data)
        for wf_id, wf_data in workflows_data.items()
    ]
    workflows.sort(key=lambda w: w.created_at, reverse=True)
    
    return WorkflowList(items=workflows, total=len(workflows))


@router.post("", response_model=Workflow, status_code=201)
async def create_workflow(workflow_data: WorkflowCreate) -> Workflow:
    """
    Create a new workflow
    
    Creates a new workflow with the provided name, description, and graph data.
    The graph data contains Vue Flow nodes and edges for workflow visualization.
    """
    data = load_workflows()
    workflows = data.get("workflows", {})
    
    workflow_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_workflow = {
        "name": workflow_data.name,
        "description": workflow_data.description,
        "graph_data": workflow_data.graph_data.model_dump(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    workflows[workflow_id] = new_workflow
    data["workflows"] = workflows
    save_workflows(data)
    
    return workflow_to_model(workflow_id, new_workflow)


@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str) -> Workflow:
    """
    Get a workflow by ID
    
    Retrieves a single workflow with full details including graph data.
    Returns 404 if workflow is not found.
    """
    data = load_workflows()
    workflows = data.get("workflows", {})
    
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    return workflow_to_model(workflow_id, workflows[workflow_id])


@router.put("/{workflow_id}", response_model=Workflow)
async def update_workflow(
    workflow_id: str,
    update_data: WorkflowUpdate,
) -> Workflow:
    """
    Update an existing workflow
    
    Updates the workflow with the provided fields.
    Unprovided fields remain unchanged.
    Returns 404 if workflow is not found.
    """
    data = load_workflows()
    workflows = data.get("workflows", {})
    
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    existing = workflows[workflow_id]
    
    # Update fields if provided
    if update_data.name is not None:
        existing["name"] = update_data.name
    if update_data.description is not None:
        existing["description"] = update_data.description
    if update_data.graph_data is not None:
        existing["graph_data"] = update_data.graph_data.model_dump()
    
    existing["updated_at"] = datetime.utcnow().isoformat()
    
    workflows[workflow_id] = existing
    data["workflows"] = workflows
    save_workflows(data)
    
    return workflow_to_model(workflow_id, existing)


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(workflow_id: str) -> None:
    """
    Delete a workflow
    
    Removes the workflow from storage.
    Returns 404 if workflow is not found.
    """
    data = load_workflows()
    workflows = data.get("workflows", {})
    
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    del workflows[workflow_id]
    data["workflows"] = workflows
    save_workflows(data)
    
    return None


def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, input_data: dict) -> StreamingResponse:
    initial_input = input_data.get("input", "")
    if not initial_input:
        raise HTTPException(status_code=400, detail="Input cannot be empty")

    workflow = await get_workflow(workflow_id)

    async def generate() -> AsyncGenerator[str, None]:
        from app.core.workflow_engine import WorkflowEngine

        engine = WorkflowEngine(workflow)
        async for event in engine.execute(initial_input):
            event_type = event.pop("type", "unknown")
            yield format_sse(event_type, event)
        yield format_sse("done", {"status": "complete"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
