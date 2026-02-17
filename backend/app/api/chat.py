"""
Chat API endpoints for SSE streaming chat.

This module provides the chat completion endpoint with SSE streaming support,
integrating RAG retrieval and DeepSeek LLM for AI-powered conversations.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.core.auth import User, get_current_user
from app.core.audit import audit_log
from app.core.config import settings
from app.core.llm import (
    estimate_message_tokens,
    get_available_models,
    get_model_context_window,
    resolve_model,
)
from app.models.user import UserRole
from app.core.rag import get_rag_pipeline
from app.middleware.rate_limit import limiter
from app.api.chat_session import (
    save_session,
    load_session,
    check_session_ownership,
    list_user_sessions,
    delete_session_by_id,
)
from app.api.chat_stream import (
    workflow_stream_generator,
    skill_stream_generator,
    stream_with_save,
)
from app.models.chat import ChatMessage, ChatRequest

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
logger = logging.getLogger(__name__)

# Constants
DEFAULT_RAG_TOP_K = 5


def parse_at_skill(message: str) -> Tuple[Optional[str], str]:
    """
    Parse @skill invocation from message.

    Pattern: ^@([a-z0-9-]+)\\s+(.+)$
    Example: "@article-summary This is an article..."
    Returns: ("article-summary", "This is an article...")

    If no @skill pattern found, returns (None, original_message).
    """
    pattern = r"^@([a-z0-9-]+)\s+(.+)$"
    match = re.match(pattern, message, re.DOTALL)
    if match:
        return match.group(1), match.group(2)
    return None, message


def build_system_prompt(has_rag: bool, retrieved_context: Optional[str] = None) -> str:
    """Build system prompt based on context."""
    base = "You are a helpful AI assistant."
    sections = [base]
    if has_rag and retrieved_context:
        sections.append(
            "Answer the user's question based on the provided context. "
            "If the context doesn't contain relevant information, say so clearly."
        )
        sections.append(f"Context:\n{retrieved_context}")
    return "\n\n".join(sections)


def _build_history_messages(
    session_messages: list[ChatMessage],
    model: str | None,
    *,
    reserved_tokens: int,
) -> list[dict[str, str]]:
    s = settings()
    context_window = get_model_context_window(model)
    base_budget = int(context_window * s.llm_context_ratio)
    history_budget = max(
        s.llm_history_token_floor, base_budget - max(0, reserved_tokens)
    )
    minimum_messages = max(0, int(s.llm_history_min_messages))

    selected: list[dict[str, str]] = []
    used_tokens = 0

    for msg in reversed(session_messages):
        candidate = {"role": msg.role, "content": msg.content}
        candidate_tokens = estimate_message_tokens([candidate])
        would_exceed = used_tokens + candidate_tokens > history_budget
        if selected and would_exceed and len(selected) >= minimum_messages:
            break
        selected.append(candidate)
        used_tokens += candidate_tokens

    selected.reverse()
    return selected


async def chat_completions(
    payload: ChatRequest,
    user: User,
    request: Request | None = None,
) -> StreamingResponse:
    """
    SSE streaming chat completion endpoint.

    Supports simple chat, RAG-enhanced chat, and workflow execution.
    """
    if not payload.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty"
        )

    # Load or create session
    session = await load_session(payload.session_id)
    user_id_str = str(user.id)
    if session is None:
        from app.models.chat import SessionHistory

        session = SessionHistory(
            session_id=payload.session_id,
            kb_id=payload.kb_id,
            workflow_id=payload.workflow_id,
            user_id=user_id_str,
        )

    # Check session ownership
    if (
        session.user_id is not None
        and session.user_id != user_id_str
        and user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this session",
        )

    # Update session metadata
    if payload.kb_id:
        session.kb_id = payload.kb_id
    if payload.workflow_id:
        session.workflow_id = payload.workflow_id
    session.user_id = user_id_str

    # Add user message to history
    user_message = ChatMessage(
        role="user", content=payload.message, timestamp=datetime.now(timezone.utc)
    )
    session.messages.append(user_message)

    # Route to appropriate handler
    if payload.workflow_id:
        if request is not None:
            audit_log(
                request=request,
                user_id=user.id,
                action="workflow_execute",
                resource_id=payload.workflow_id,
            )
        history_for_workflow = _build_history_messages(
            session.messages[:-1],
            payload.model,
            reserved_tokens=0,
        )
        return StreamingResponse(
            workflow_stream_generator(
                payload,
                session,
                user,
                conversation_history=history_for_workflow,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    skill_name, remaining_text = parse_at_skill(payload.message)
    if skill_name:
        return StreamingResponse(
            skill_stream_generator(skill_name, remaining_text, session, user),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Prepare messages for LLM
    messages_for_llm: List[dict[str, Any]] = []

    # Build system prompt with RAG context if available
    retrieved_results: List[dict[str, Any]] = []
    retrieved_context = None
    if payload.kb_id:
        try:
            rag_pipeline = get_rag_pipeline()
            retrieved_results = await rag_pipeline.search(
                payload.kb_id, payload.message, top_k=DEFAULT_RAG_TOP_K
            )
            if retrieved_results:
                context_parts = []
                for i, r in enumerate(retrieved_results[:3], 1):
                    context_parts.append(f"[{i}] {r['text']}")
                retrieved_context = "\n\n".join(context_parts)
        except Exception:
            logger.warning(
                "RAG retrieval failed for kb_id=%s", payload.kb_id, exc_info=True
            )

    system_prompt = build_system_prompt(bool(payload.kb_id), retrieved_context)
    system_message = {"role": "system", "content": system_prompt}
    system_tokens = estimate_message_tokens([system_message])
    messages_for_llm.append(system_message)
    messages_for_llm.extend(
        _build_history_messages(
            session.messages,
            payload.model,
            reserved_tokens=system_tokens,
        )
    )

    return StreamingResponse(
        stream_with_save(
            payload,
            session,
            messages_for_llm,
            retrieved_results,
            user_id=user.id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/completions")
@limiter.limit("10/minute")
async def chat_completions_endpoint(
    request: Request,
    payload: ChatRequest,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    return await chat_completions(payload, user, request=request)


@router.get("/models")
async def list_models(user: User = Depends(get_current_user)) -> dict[str, Any]:
    models = [item for item in get_available_models() if item["enabled"]]
    default_model: str | None = None
    try:
        provider, model_name = resolve_model(None)
        default_model = f"{provider}:{model_name}"
    except ValueError:
        default_model = None
    return {
        "items": models,
        "default_model": default_model,
        "total": len(models),
    }


@router.get("/sessions")
async def list_sessions(
    user: User = Depends(get_current_user),
) -> dict[str, list[dict[str, Any]]]:
    """List chat sessions for the current user."""
    sessions = await list_user_sessions(user)
    return {"sessions": sessions}


@router.get("/sessions/{session_id}")
async def get_session_history(
    session_id: str, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Get chat history for a session."""
    try:
        session = await load_session(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session_id: {session_id}",
        )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )

    if not check_session_ownership(session, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this session",
        )

    return {
        "session_id": session.session_id,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
            }
            for msg in session.messages
        ],
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "kb_id": session.kb_id,
        "workflow_id": session.workflow_id,
        "user_id": session.user_id,
        "message_count": len(session.messages),
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str, user: User = Depends(get_current_user)
) -> dict[str, str]:
    """Delete a chat session and its history."""
    try:
        session = await load_session(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session_id: {session_id}",
        )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )

    if not check_session_ownership(session, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this session",
        )

    deleted = await delete_session_by_id(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session.",
        )
    return {
        "status": "success",
        "message": f"Session '{session_id}' deleted successfully",
    }
