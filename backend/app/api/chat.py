"""
Chat API endpoints for SSE streaming chat.

This module provides the chat completion endpoint with SSE streaming support,
integrating RAG retrieval and DeepSeek LLM for AI-powered conversations.
"""
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.auth import User, get_current_user
from app.models.user import UserRole
from app.core.rag import get_rag_pipeline
from app.api.chat_session import (
    SESSIONS_DIR,
    save_session,
    load_session,
    check_session_ownership,
    get_session_path,
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
MAX_HISTORY_MESSAGES = 10
DEFAULT_RAG_TOP_K = 5


def parse_at_skill(message: str) -> Tuple[Optional[str], str]:
    """
    Parse @skill invocation from message.

    Pattern: ^@([a-z0-9-]+)\s+(.+)$
    Example: "@article-summary This is an article..."
    Returns: ("article-summary", "This is an article...")

    If no @skill pattern found, returns (None, original_message).
    """
    pattern = r'^@([a-z0-9-]+)\s+(.+)$'
    match = re.match(pattern, message, re.DOTALL)
    if match:
        return match.group(1), match.group(2)
    return None, message


def build_system_prompt(
    has_rag: bool,
    retrieved_context: Optional[str] = None
) -> str:
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


@router.post("/completions")
async def chat_completions(
    request: ChatRequest,
    user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    SSE streaming chat completion endpoint.

    Supports simple chat, RAG-enhanced chat, and workflow execution.
    """
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )

    # Load or create session
    session = load_session(request.session_id)
    user_id_str = str(user.id)
    if session is None:
        from app.models.chat import SessionHistory
        session = SessionHistory(
            session_id=request.session_id,
            kb_id=request.kb_id,
            workflow_id=request.workflow_id,
            user_id=user_id_str
        )

    # Check session ownership
    if session.user_id is not None and session.user_id != user_id_str and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this session"
        )

    # Update session metadata
    if request.kb_id:
        session.kb_id = request.kb_id
    if request.workflow_id:
        session.workflow_id = request.workflow_id
    session.user_id = user_id_str

    # Add user message to history
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.now(timezone.utc)
    )
    session.messages.append(user_message)

    # Route to appropriate handler
    if request.workflow_id:
        return StreamingResponse(
            workflow_stream_generator(request, session, user),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    skill_name, remaining_text = parse_at_skill(request.message)
    if skill_name:
        return StreamingResponse(
            skill_stream_generator(skill_name, remaining_text, session, user),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # Prepare messages for LLM
    messages_for_llm: List[dict] = []

    # Build system prompt with RAG context if available
    retrieved_results: List[dict] = []
    retrieved_context = None
    if request.kb_id:
        try:
            rag_pipeline = get_rag_pipeline()
            retrieved_results = await rag_pipeline.search(request.kb_id, request.message, top_k=DEFAULT_RAG_TOP_K)
            if retrieved_results:
                context_parts = []
                for i, r in enumerate(retrieved_results[:3], 1):
                    context_parts.append(f"[{i}] {r['text']}")
                retrieved_context = "\n\n".join(context_parts)
        except Exception:
            logger.warning("RAG retrieval failed for kb_id=%s", request.kb_id, exc_info=True)

    system_prompt = build_system_prompt(
        bool(request.kb_id),
        retrieved_context
    )
    messages_for_llm.append({"role": "system", "content": system_prompt})

    # Add conversation history (last 10 messages)
    for msg in session.messages[-MAX_HISTORY_MESSAGES:]:
        messages_for_llm.append({"role": msg.role, "content": msg.content})

    return StreamingResponse(
        stream_with_save(request, session, messages_for_llm, retrieved_results),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/sessions")
async def list_sessions(user: User = Depends(get_current_user)) -> dict:
    """List chat sessions for the current user."""
    sessions = []
    user_id_str = str(user.id)

    for path in SESSIONS_DIR.glob("*.json"):
        session_id = path.stem
        session = load_session(session_id)
        if not session:
            continue

        # Filter by ownership (admin sees all)
        if user.role != UserRole.ADMIN:
            if session.user_id is not None and session.user_id != user_id_str:
                continue

        title = ""
        for msg in session.messages:
            if msg.role == "user":
                title = msg.content
                break
        sessions.append({
            "session_id": session.session_id,
            "title": title,
            "created_at": session.created_at.isoformat(),
            "updated_at": (
                session.updated_at.isoformat()
                if session.updated_at
                else session.created_at.isoformat()
            ),
            "message_count": len(session.messages),
            "kb_id": session.kb_id,
            "workflow_id": session.workflow_id,
            "user_id": session.user_id
        })

    sessions.sort(key=lambda s: s["updated_at"], reverse=True)
    return {"sessions": sessions}


@router.get("/sessions/{session_id}")
async def get_session_history(
    session_id: str,
    user: User = Depends(get_current_user)
) -> dict:
    """Get chat history for a session."""
    try:
        session = load_session(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session_id: {session_id}"
        )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )

    if not check_session_ownership(session, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this session"
        )

    return {
        "session_id": session.session_id,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
            }
            for msg in session.messages
        ],
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "kb_id": session.kb_id,
        "workflow_id": session.workflow_id,
        "user_id": session.user_id,
        "message_count": len(session.messages)
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_user)
) -> dict:
    """Delete a chat session and its history."""
    try:
        session = load_session(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session_id: {session_id}"
        )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )

    if not check_session_ownership(session, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this session"
        )

    try:
        session_path = get_session_path(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session_id: {session_id}"
        )
    try:
        session_path.unlink()
        return {
            "status": "success",
            "message": f"Session '{session_id}' deleted successfully"
        }
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )
