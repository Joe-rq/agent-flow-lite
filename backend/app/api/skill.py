"""
Skill API endpoints for CRUD operations and execution.

Provides RESTful endpoints for managing skills:
- GET GET /api/v1/skills - List all skills
- GET /api/v1/skills/{name} - Get skill details
- POST /api/v1/skills - Create new skill
- PUT /api/v1/skills/{name} - Update skill content
- DELETE /api/v1/skills/{name} - Delete skill
- POST /api/v1/skills/{name}/run - Execute skill with SSE streaming
"""
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.config import settings
from app.core.skill.skill_executor import SkillExecutor, format_sse_event, get_skill_executor
from app.core.skill.skill_loader import SkillLoader, SkillValidationError
from app.models.skill import (
    SkillCreateRequest,
    SkillDetail,
    SkillListResponse,
    SkillRunRequest,
    SkillSummary,
    SkillUpdateRequest,
)
from app.core.auth import User, get_current_user
from app.models.user import UserRole

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])

# Initialize skill loader with skills directory
SKILLS_DIR = Path(__file__).parent.parent.parent / "data" / "skills"
skill_loader = SkillLoader(SKILLS_DIR)


def _handle_validation_error(exc: SkillValidationError) -> HTTPException:
    """Convert SkillValidationError to HTTPException with appropriate status code."""
    status_code = status.HTTP_400_BAD_REQUEST
    if "not found" in exc.message.lower():
        status_code = status.HTTP_404_NOT_FOUND
    elif "already exists" in exc.message.lower() or "conflicts" in exc.message.lower():
        status_code = status.HTTP_409_CONFLICT

    return HTTPException(
        status_code=status_code,
        detail={"field": exc.field, "message": exc.message},
    )


@router.get("", response_model=SkillListResponse)
async def list_skills(user: User = Depends(get_current_user)) -> SkillListResponse:
    """
    List all available skills.

    Returns a list of skill summaries sorted by updated_at (newest first).
    Admin users see all skills, regular users only see their own.
    """
    try:
        # Admin sees all, regular users see only their own
        user_id_filter = None if user.role == UserRole.ADMIN else str(user.id)
        skills = skill_loader.list_skills(user_id=user_id_filter)
        return SkillListResponse(skills=skills, total=len(skills))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skills: {str(exc)}",
        ) from exc


@router.get("/{name}", response_model=SkillDetail)
async def get_skill(name: str, user: User = Depends(get_current_user)) -> SkillDetail:
    """
    Get detailed information about a specific skill.

    - **name**: Skill name (path parameter)
    """
    try:
        return skill_loader.get_skill(name)
    except SkillValidationError as exc:
        raise _handle_validation_error(exc) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill: {str(exc)}",
        ) from exc


@router.post("", response_model=SkillDetail, status_code=status.HTTP_201_CREATED)
async def create_skill(data: SkillCreateRequest, user: User = Depends(get_current_user)) -> SkillDetail:
    """
    Create a new skill.

    - **name**: Skill name (used as folder name)
    - **content**: Complete SKILL.md file content

    The skill name must be unique, lowercase, and contain only letters,
    numbers, and hyphens. Cannot start or end with hyphen.
    """
    try:
        return skill_loader.create_skill(data.name, data.content, user_id=str(user.id))
    except SkillValidationError as exc:
        raise _handle_validation_error(exc) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill: {str(exc)}",
        ) from exc


@router.put("/{name}", response_model=SkillDetail)
async def update_skill(name: str, data: SkillUpdateRequest, user: User = Depends(get_current_user)) -> SkillDetail:
    """
    Update an existing skill's SKILL.md content.

    - **name**: Skill name (path parameter, cannot be changed)
    - **content**: New SKILL.md file content

    Note: The skill name cannot be changed via update. To rename,
    delete and recreate the skill.
    """
    try:
        return skill_loader.update_skill(name, data.content)
    except SkillValidationError as exc:
        raise _handle_validation_error(exc) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill: {str(exc)}",
        ) from exc


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(name: str, user: User = Depends(get_current_user)) -> None:
    """
    Delete a skill and all its contents.

    - **name**: Skill name to delete

    This permanently removes the skill folder and all files within it.
    """
    try:
        skill_loader.delete_skill(name)
    except SkillValidationError as exc:
        raise _handle_validation_error(exc) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete skill: {str(exc)}",
        ) from exc


async def _execute_skill_stream(
    skill: SkillDetail,
    inputs: dict[str, str],
    executor: SkillExecutor,
) -> AsyncGenerator[str, None]:
    """Execute skill and yield SSE events."""
    try:
        async for event in executor.execute(skill, inputs):
            yield event
    except Exception as exc:
        # Yield error event if execution fails
        yield format_sse_event("done", {
            "status": "error",
            "message": f"Skill execution failed: {str(exc)}"
        })


@router.post("/{name}/run")
async def run_skill(name: str, data: SkillRunRequest, user: User = Depends(get_current_user)) -> StreamingResponse:
    """
    Execute a skill with the provided inputs.

    - **name**: Skill name to execute
    - **inputs**: Dictionary of input variable values

    Returns a Server-Sent Events (SSE) stream with the following event types:
    - `thought`: Execution status updates (validation, substitution, retrieval, generation)
    - `token`: LLM-generated content chunks
    - `citation`: Source citations from knowledge base retrieval
    - `done`: Completion marker with status
    """
    try:
        # Load the skill
        skill = skill_loader.get_skill(name)
    except SkillValidationError as exc:
        raise _handle_validation_error(exc) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load skill: {str(exc)}",
        ) from exc

    # Get skill executor
    executor = get_skill_executor()

    # Return SSE streaming response
    return StreamingResponse(
        _execute_skill_stream(skill, data.inputs, executor),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
