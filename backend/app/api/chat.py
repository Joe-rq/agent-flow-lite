"""
Chat API endpoints for SSE streaming chat.

This module provides the chat completion endpoint with SSE streaming support,
integrating RAG retrieval and DeepSeek LLM for AI-powered conversations.
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from filelock import FileLock

from app.core.auth import User, get_current_user
from app.models.user import UserRole
from app.core.llm import chat_completion_stream
from app.core.rag import get_rag_pipeline
from app.core.workflow_engine import WorkflowEngine
from app.core.zep import zep_client
from app.core.skill_loader import SkillLoader, SkillValidationError
from app.core.skill_executor import get_skill_executor
from app.api.workflow import get_workflow
from app.models.chat import ChatMessage, ChatRequest, SessionHistory

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

SESSIONS_DIR = Path(__file__).parent.parent.parent / "data" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

SKILLS_DIR = Path(__file__).parent.parent.parent.parent.parent / "skills"
skill_loader = SkillLoader(SKILLS_DIR)


def get_session_path(session_id: str) -> Path:
    """Get the file path for a session."""
    return SESSIONS_DIR / f"{session_id}.json"


def check_session_ownership(session: SessionHistory, user: User) -> bool:
    """
    Check if a user owns a session or is an admin.
    
    Args:
        session: The session to check
        user: The current authenticated user
        
    Returns:
        True if user owns the session or is admin, False otherwise
    """
    # Admin can access any session
    if user.role == UserRole.ADMIN:
        return True
    
    # If session has no user_id, treat as orphaned - allow access for backward compatibility
    # but ideally should be migrated
    if session.user_id is None:
        return True
    
    # Check if user owns the session
    return session.user_id == str(user.id)


def load_session(session_id: str) -> Optional[SessionHistory]:
    """Load session history from JSON file."""
    session_path = get_session_path(session_id)
    lock = FileLock(str(session_path) + ".lock")
    with lock:
        if not session_path.exists():
            return None
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Parse timestamps back to datetime objects
                for msg in data.get("messages", []):
                    if msg.get("timestamp"):
                        msg["timestamp"] = datetime.fromisoformat(msg["timestamp"])
                if data.get("created_at"):
                    data["created_at"] = datetime.fromisoformat(data["created_at"])
                if data.get("updated_at"):
                    data["updated_at"] = datetime.fromisoformat(data["updated_at"])
                return SessionHistory(**data)
        except (json.JSONDecodeError, IOError, ValueError):
            return None


def save_session(session: SessionHistory) -> None:
    """Save session history to JSON file."""
    session_path = get_session_path(session.session_id)
    session.updated_at = datetime.utcnow()
    lock = FileLock(str(session_path) + ".lock")
    with lock:
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(session.model_dump(mode="json"), f, ensure_ascii=False, indent=2)


def format_sse_event(event: str, data: dict) -> str:
    """Format data as SSE event string."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def build_excerpt(text: str, limit: int = 200) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def parse_at_skill(message: str) -> Tuple[Optional[str], str]:
    """
    Parse @skill invocation from message.

    Pattern: ^@([a-z0-9-]+)\s+(.+)$
    Example: "@article-summary This is an article..."
    Returns: ("article-summary", "This is an article...")

    If no @skill pattern found, returns (None, original_message).

    Args:
        message: User input message

    Returns:
        Tuple of (skill_name or None, remaining_text)
    """
    pattern = r'^@([a-z0-9-]+)\s+(.+)$'
    match = re.match(pattern, message, re.DOTALL)
    if match:
        return match.group(1), match.group(2)
    return None, message


async def skill_stream_generator(
    skill_name: str,
    remaining_text: str,
    session: SessionHistory,
    user: User
) -> AsyncGenerator[str, None]:
    """
    Generate SSE stream for @skill execution.

    Args:
        skill_name: Name of the skill to execute
        remaining_text: Text after @skill (mapped to first required input)
        session: Current chat session
        user: Current authenticated user

    Yields:
        SSE event strings (thought, token, citation, done)
    """
    zep = zep_client()
    executor = get_skill_executor()

    try:
        # Load the skill
        yield format_sse_event("thought", {
            "type": "skill",
            "status": "start",
            "skill_name": skill_name
        })

        try:
            skill = skill_loader.get_skill(skill_name)
        except SkillValidationError as e:
            yield format_sse_event("thought", {
                "type": "skill",
                "status": "error",
                "error": str(e)
            })
            yield format_sse_event("done", {
                "status": "error",
                "message": f"Skill '{skill_name}' not found"
            })
            return

        yield format_sse_event("thought", {
            "type": "skill",
            "status": "loaded",
            "skill_name": skill.name,
            "description": skill.description
        })

        # Build inputs: map remaining_text to first required input
        inputs: dict = {}
        skill_inputs = skill.inputs or []

        # Find first required input
        first_required = None
        for inp in skill_inputs:
            if inp.required:
                first_required = inp.name
                break

        # If no required input, use first input
        if first_required is None and skill_inputs:
            first_required = skill_inputs[0].name

        if first_required:
            inputs[first_required] = remaining_text
        else:
            # Skill has no inputs, treat remaining_text as the entire prompt
            pass

        # Execute skill
        full_output = ""
        async for event in executor.execute(skill, inputs):
            yield event

            # Accumulate output for session save
            if event.startswith("event: token"):
                try:
                    lines = event.strip().split("\n")
                    for line in lines:
                        if line.startswith("data: "):
                            data = json.loads(line[6:])
                            full_output += data.get("content", "")
                except (json.JSONDecodeError, IndexError):
                    pass

        # Save to session history
        if full_output:
            assistant_message = ChatMessage(
                role="assistant",
                content=full_output,
                timestamp=datetime.utcnow()
            )
            session.messages.append(assistant_message)
            save_session(session)

            if zep.enabled:
                zep_session_id = get_zep_session_id(str(user.id), session.session_id)
                zep.add_messages(
                    zep_session_id,
                    [{
                        "role_type": "assistant",
                        "role": "Assistant",
                        "content": full_output
                    }]
                )

    except Exception as e:
        yield format_sse_event("thought", {
            "type": "skill",
            "status": "error",
            "error": str(e)
        })
        yield format_sse_event("done", {
            "status": "error",
            "message": f"Skill execution failed: {str(e)}"
        })


def build_system_prompt(
    has_rag: bool,
    retrieved_context: Optional[str] = None,
    memory_context: Optional[str] = None
) -> str:
    """Build system prompt based on context."""
    base = "You are a helpful AI assistant."
    sections = [base]
    if memory_context:
        sections.append(f"User Memory:\n{memory_context}")
    if has_rag and retrieved_context:
        sections.append(
            "Answer the user's question based on the provided context. "
            "If the context doesn't contain relevant information, say so clearly."
        )
        sections.append(f"Context:\n{retrieved_context}")
    return "\n\n".join(sections)


async def chat_stream_generator(
    request: ChatRequest,
    messages: List[dict],
    pre_retrieved_results: Optional[List[dict]] = None
) -> AsyncGenerator[str, None]:
    """
    Generate SSE stream for chat completion.
    
    Events:
    - thought: RAG retrieval process
    - token: LLM generated token
    - citation: Source metadata from RAG
    - done: Completion marker
    """
    retrieved_results: List[dict] = pre_retrieved_results or []
    has_error = False
    error_message = ""
    
    try:
        # Step 1: RAG Retrieval (if kb_id provided)
        if request.kb_id:
            yield format_sse_event("thought", {
                "type": "retrieval",
                "status": "start",
                "kb_id": request.kb_id,
                "query": request.message
            })

            yield format_sse_event("thought", {
                "type": "retrieval",
                "status": "searching",
                "kb_id": request.kb_id,
                "query": request.message
            })

            if pre_retrieved_results is None:
                try:
                    rag_pipeline = get_rag_pipeline()
                    retrieved_results = rag_pipeline.search(
                        request.kb_id, request.message, top_k=5
                    )
                except Exception as e:
                    yield format_sse_event("thought", {
                        "type": "retrieval",
                        "status": "error",
                        "kb_id": request.kb_id,
                        "query": request.message,
                        "error": str(e)
                    })
                    retrieved_results = []

            top_results = [
                {
                    "text": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
                    "doc_id": r["metadata"].get("doc_id", ""),
                    "score": r["score"]
                }
                for r in retrieved_results[:3]
            ]

            yield format_sse_event("thought", {
                "type": "retrieval",
                "status": "complete",
                "kb_id": request.kb_id,
                "query": request.message,
                "results_count": len(retrieved_results),
                "top_results": top_results
            })

            if retrieved_results:
                sources = [
                    {
                        "doc_id": r["metadata"].get("doc_id", ""),
                        "chunk_index": r["metadata"].get("chunk_index", 0),
                        "score": r["score"],
                        "text": build_excerpt(r["text"])
                    }
                    for r in retrieved_results
                ]
                yield format_sse_event("citation", {"sources": sources})
        
        # Step 2: Stream LLM tokens
        async for token in chat_completion_stream(messages, temperature=0.7):
            yield format_sse_event("token", {"content": token})
        
    except Exception as e:
        has_error = True
        error_message = str(e)
        yield format_sse_event("token", {"content": f"\n[Error: {str(e)}]"})
    
    # Step 3: Done event
    if has_error:
        yield format_sse_event("done", {
            "status": "error",
            "message": error_message
        })
    else:
        yield format_sse_event("done", {
            "status": "success",
            "message": "Chat completed successfully"
        })


def get_zep_session_id(user_id: str, session_id: str) -> str:
    """
    Generate namespaced session ID for Zep operations.
    
    Format: {user_id}::{session_id}
    This ensures session isolation between users in Zep.
    """
    return f"{user_id}::{session_id}"


async def workflow_stream_generator(
    request: ChatRequest, session: SessionHistory, user: User
) -> AsyncGenerator[str, None]:
    zep = zep_client()
    if not request.workflow_id:
        yield format_sse_event("error", {"message": "Workflow ID is required"})
        yield format_sse_event("done", {"status": "error", "message": "Workflow ID is required"})
        return

    try:
        workflow = await get_workflow(request.workflow_id)
    except HTTPException as exc:
        yield format_sse_event("error", {"message": str(exc.detail)})
        yield format_sse_event("done", {"status": "error", "message": str(exc.detail)})
        return

    engine = WorkflowEngine(workflow)
    full_output = ""

    async for event in engine.execute(request.message):
        event_type = event.get("type")

        if event_type == "workflow_start":
            yield format_sse_event("thought", {
                "type": "workflow",
                "status": "start",
                "workflow_name": event.get("workflow_name")
            })

        elif event_type == "node_start":
            yield format_sse_event("thought", {
                "type": "node",
                "status": "start",
                "node_id": event.get("node_id"),
                "node_type": event.get("node_type")
            })

        elif event_type == "token":
            content = event.get("content", "")
            full_output += content
            yield format_sse_event("token", {"content": content})

        elif event_type == "thought":
            payload = {"type": event.get("type_detail", "info")}
            payload.update({k: v for k, v in event.items() if k not in ("type", "type_detail")})
            yield format_sse_event("thought", payload)

        elif event_type == "node_complete":
            yield format_sse_event("thought", {
                "type": "node",
                "status": "complete",
                "node_id": event.get("node_id")
            })

        elif event_type in ("node_error", "workflow_error"):
            message = event.get("error", "Unknown workflow error")
            yield format_sse_event("error", {"message": message})
            yield format_sse_event("done", {"status": "error", "message": message})
            return

        elif event_type == "workflow_complete":
            final_output = event.get("final_output", full_output)
            assistant_message = ChatMessage(
                role="assistant",
                content=str(final_output),
                timestamp=datetime.utcnow()
            )
            session.messages.append(assistant_message)
            save_session(session)
            if zep.enabled:
                zep_session_id = get_zep_session_id(str(user.id), session.session_id)
                zep.add_messages(
                    zep_session_id,
                    [{
                        "role_type": "assistant",
                        "role": "Assistant",
                        "content": str(final_output)
                    }]
                )
            yield format_sse_event("done", {
                "status": "success",
                "message": "Workflow completed"
            })
            return

    try:
        workflow = await get_workflow(request.workflow_id)
    except HTTPException as exc:
        yield format_sse_event("error", {"message": str(exc.detail)})
        yield format_sse_event("done", {"status": "error", "message": str(exc.detail)})
        return

    engine = WorkflowEngine(workflow)
    full_output = ""

    async for event in engine.execute(request.message):
        event_type = event.get("type")

        if event_type == "workflow_start":
            yield format_sse_event("thought", {
                "type": "workflow",
                "status": "start",
                "workflow_name": event.get("workflow_name")
            })

        elif event_type == "node_start":
            yield format_sse_event("thought", {
                "type": "node",
                "status": "start",
                "node_id": event.get("node_id"),
                "node_type": event.get("node_type")
            })

        elif event_type == "token":
            content = event.get("content", "")
            full_output += content
            yield format_sse_event("token", {"content": content})

        elif event_type == "thought":
            payload = {"type": event.get("type_detail", "info")}
            payload.update({k: v for k, v in event.items() if k not in ("type", "type_detail")})
            yield format_sse_event("thought", payload)

        elif event_type == "node_complete":
            yield format_sse_event("thought", {
                "type": "node",
                "status": "complete",
                "node_id": event.get("node_id")
            })

        elif event_type in ("node_error", "workflow_error"):
            message = event.get("error", "Unknown workflow error")
            yield format_sse_event("error", {"message": message})
            yield format_sse_event("done", {"status": "error", "message": message})
            return

        elif event_type == "workflow_complete":
            final_output = event.get("final_output", full_output)
            assistant_message = ChatMessage(
                role="assistant",
                content=str(final_output),
                timestamp=datetime.utcnow()
            )
            session.messages.append(assistant_message)
            save_session(session)
            if zep.enabled and request.user_id:
                zep.add_messages(
                    session.session_id,
                    [{
                        "role_type": "assistant",
                        "role": "Assistant",
                        "content": str(final_output)
                    }]
                )
            yield format_sse_event("done", {
                "status": "success",
                "message": "Workflow completed"
            })
            return


@router.post("/completions")
async def chat_completions(
    request: ChatRequest,
    user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    SSE streaming chat completion endpoint.
    
    Supports simple chat, RAG-enhanced chat, and workflow execution.
    
    Request body:
    - session_id: Session identifier for conversation continuity
    - message: User's input message
    - kb_id: Optional knowledge base ID for RAG retrieval
    - workflow_id: Optional workflow ID for workflow execution
    
    SSE Events:
    - event: thought - RAG retrieval status and results
    - event: token - LLM generated content chunks
    - event: citation - Source metadata from retrieved documents
    - event: done - Completion marker
    """
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )

    zep = zep_client()
    
    # Load or create session
    session = load_session(request.session_id)
    user_id_str = str(user.id)
    if session is None:
        session = SessionHistory(
            session_id=request.session_id,
            kb_id=request.kb_id,
            workflow_id=request.workflow_id,
            user_id=user_id_str
        )

    # Check session ownership if session exists and has an owner
    if session.user_id is not None and session.user_id != user_id_str and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this session"
        )

    # Update session metadata if provided
    if request.kb_id:
        session.kb_id = request.kb_id
    if request.workflow_id:
        session.workflow_id = request.workflow_id
    session.user_id = user_id_str

    # Add user message to history
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.utcnow()
    )
    session.messages.append(user_message)

    # Use namespaced session ID for Zep operations
    zep_session_id = get_zep_session_id(user_id_str, request.session_id)
    if zep.enabled:
        zep.ensure_user_session(user_id_str, zep_session_id)
        zep.add_messages(
            zep_session_id,
            [{
                "role_type": "user",
                "role": user_id_str,
                "content": request.message
            }]
        )
    
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
            retrieved_results = rag_pipeline.search(request.kb_id, request.message, top_k=5)
            if retrieved_results:
                context_parts = []
                for i, r in enumerate(retrieved_results[:3], 1):
                    context_parts.append(f"[{i}] {r['text']}")
                retrieved_context = "\n\n".join(context_parts)
        except Exception:
            pass  # Continue without RAG context if retrieval fails
    
    memory_context = ""
    if zep.enabled and request.user_id:
        memory_context = zep.get_memory_context(request.session_id)
    system_prompt = build_system_prompt(
        bool(request.kb_id),
        retrieved_context,
        memory_context
    )
    messages_for_llm.append({"role": "system", "content": system_prompt})
    
    # Add conversation history (last 10 messages)
    for msg in session.messages[-10:]:
        messages_for_llm.append({"role": msg.role, "content": msg.content})
    
    # Create the streaming response
    async def stream_with_save():
        """Stream response and save to session history."""
        assistant_content = ""
        
        async for chunk in chat_stream_generator(request, messages_for_llm, retrieved_results):
            # Parse token events to accumulate response
            if chunk.startswith("event: token"):
                try:
                    lines = chunk.strip().split("\n")
                    for line in lines:
                        if line.startswith("data: "):
                            data = json.loads(line[6:])
                            assistant_content += data.get("content", "")
                except (json.JSONDecodeError, IndexError):
                    pass
            yield chunk
        
        # Save assistant response to session
        if assistant_content:
            assistant_message = ChatMessage(
                role="assistant",
                content=assistant_content,
                timestamp=datetime.utcnow()
            )
            session.messages.append(assistant_message)
            save_session(session)
            if zep.enabled and request.user_id:
                zep.add_messages(
                    request.session_id,
                    [{
                        "role_type": "assistant",
                        "role": "Assistant",
                        "content": assistant_content
                    }]
                )
    
    return StreamingResponse(
        stream_with_save(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/sessions")
async def list_sessions(user: User = Depends(get_current_user)) -> dict:
    """
    List chat sessions for the current user.
    
    - Regular users see only their own sessions
    - Admin users see all sessions
    """
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
    """
    Get chat history for a session.
    
    - **session_id**: Session identifier
    - Users can only access their own sessions (admins can access any)
    """
    session = load_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )

    # Check ownership
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
    """
    Delete a chat session and its history.

    - **session_id**: Session identifier to delete
    - Users can only delete their own sessions (admins can delete any)
    """
    session = load_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )

    # Check ownership
    if not check_session_ownership(session, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this session"
        )

    session_path = get_session_path(session_id)
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
