"""
Chat API endpoints for SSE streaming chat.

This module provides the chat completion endpoint with SSE streaming support,
integrating RAG retrieval and DeepSeek LLM for AI-powered conversations.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, List, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from filelock import FileLock

from app.core.llm import chat_completion_stream
from app.core.rag import get_rag_pipeline
from app.core.workflow_engine import WorkflowEngine
from app.api.workflow import get_workflow
from app.models.chat import ChatMessage, ChatRequest, SessionHistory

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

SESSIONS_DIR = Path(__file__).parent.parent.parent / "data" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def get_session_path(session_id: str) -> Path:
    """Get the file path for a session."""
    return SESSIONS_DIR / f"{session_id}.json"


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


def build_system_prompt(has_rag: bool, retrieved_context: Optional[str] = None) -> str:
    """Build system prompt based on context."""
    if has_rag and retrieved_context:
        return (
            "You are a helpful AI assistant. Answer the user's question based on "
            "the provided context. If the context doesn't contain relevant information, "
            "say so clearly.\n\n"
            f"Context:\n{retrieved_context}"
        )
    return "You are a helpful AI assistant."


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
                        "score": r["score"]
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


async def workflow_stream_generator(
    request: ChatRequest, session: SessionHistory
) -> AsyncGenerator[str, None]:
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
            yield format_sse_event("done", {
                "status": "success",
                "message": "Workflow completed"
            })
            return


@router.post("/completions")
async def chat_completions(request: ChatRequest) -> StreamingResponse:
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
    
    # Load or create session
    session = load_session(request.session_id)
    if session is None:
        session = SessionHistory(
            session_id=request.session_id,
            kb_id=request.kb_id,
            workflow_id=request.workflow_id
        )
    
    # Update session metadata if provided
    if request.kb_id:
        session.kb_id = request.kb_id
    if request.workflow_id:
        session.workflow_id = request.workflow_id
    
    # Add user message to history
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.utcnow()
    )
    session.messages.append(user_message)
    
    if request.workflow_id:
        return StreamingResponse(
            workflow_stream_generator(request, session),
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
    
    system_prompt = build_system_prompt(bool(request.kb_id), retrieved_context)
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
async def list_sessions() -> dict:
    sessions = []
    for path in SESSIONS_DIR.glob("*.json"):
        session_id = path.stem
        session = load_session(session_id)
        if not session:
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
            "workflow_id": session.workflow_id
        })

    sessions.sort(key=lambda s: s["updated_at"], reverse=True)
    return {"sessions": sessions}


@router.get("/sessions/{session_id}")
async def get_session_history(session_id: str) -> dict:
    """
    Get chat history for a session.
    
    - **session_id**: Session identifier
    """
    session = load_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
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
        "message_count": len(session.messages)
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    """
    Delete a chat session and its history.
    
    - **session_id**: Session identifier to delete
    """
    session_path = get_session_path(session_id)
    if not session_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
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
