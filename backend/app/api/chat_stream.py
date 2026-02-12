"""
Chat SSE stream generators for workflow, skill, and chat completion events.

This module provides async generators that yield SSE events for different
chat interaction modes including workflow execution, skill invocation,
and standard chat completion with RAG retrieval.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional

from fastapi import HTTPException

from app.core.llm import chat_completion_stream
from app.core.paths import SKILLS_DIR
from app.core.rag import get_rag_pipeline
from app.core.skill.skill_loader import SkillLoader, SkillValidationError
from app.core.skill.skill_executor import get_skill_executor
from app.core.workflow.workflow_engine import WorkflowEngine
from app.api.workflow import get_workflow
from app.api.chat_session import save_session, EXCERPT_LIMIT
from app.models.chat import ChatMessage, ChatRequest, SessionHistory
from app.models.user import User
from app.utils.sse import format_sse_event

logger = logging.getLogger(__name__)

# Constants
DEFAULT_RAG_TOP_K = 5
LLM_STREAM_TIMEOUT = 180  # seconds, for single LLM call
WORKFLOW_TIMEOUT = 300  # seconds, for entire workflow execution

skill_loader = SkillLoader(SKILLS_DIR)


def build_excerpt(text: str, limit: int = EXCERPT_LIMIT) -> str:
    """Build excerpt from text with character limit."""
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


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
        async with asyncio.timeout(LLM_STREAM_TIMEOUT):
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
                        logger.warning("Failed to parse SSE token data")

        # Save to session history
        if full_output:
            assistant_message = ChatMessage(
                role="assistant",
                content=full_output,
                timestamp=datetime.now(timezone.utc)
            )
            session.messages.append(assistant_message)
            save_session(session)

    except TimeoutError:
        logger.warning("Skill execution timed out after %ds", LLM_STREAM_TIMEOUT)
        yield format_sse_event("error", {"message": f"Skill execution timed out ({LLM_STREAM_TIMEOUT}s)"})
        yield format_sse_event("done", {"status": "error", "message": "Timeout"})

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
                    retrieved_results = await rag_pipeline.search(
                        request.kb_id, request.message, top_k=DEFAULT_RAG_TOP_K
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
                    "text": r["text"][:EXCERPT_LIMIT] + "..."
                    if len(r["text"]) > EXCERPT_LIMIT else r["text"],
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
        async with asyncio.timeout(LLM_STREAM_TIMEOUT):
            async for token in chat_completion_stream(messages, temperature=0.7):
                yield format_sse_event("token", {"content": token})

    except TimeoutError:
        has_error = True
        error_message = f"LLM response timed out ({LLM_STREAM_TIMEOUT}s)"
        logger.warning("Chat LLM stream timed out after %ds", LLM_STREAM_TIMEOUT)
        yield format_sse_event("token", {"content": f"\n[Error: {error_message}]"})

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


async def stream_with_save(
    request: ChatRequest,
    session: SessionHistory,
    messages_for_llm: List[dict],
    retrieved_results: List[dict]
) -> AsyncGenerator[str, None]:
    """
    Stream response and save to session history.

    Args:
        request: Chat request
        session: Current session
        messages_for_llm: Messages formatted for LLM
        retrieved_results: Pre-retrieved RAG results

    Yields:
        SSE event strings
    """
    assistant_content = ""

    async for chunk in chat_stream_generator(request, messages_for_llm, retrieved_results):
        if chunk.startswith("event: token"):
            try:
                lines = chunk.strip().split("\n")
                for line in lines:
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        assistant_content += data.get("content", "")
            except (json.JSONDecodeError, IndexError):
                logger.warning("Failed to parse SSE token data")
        yield chunk

    # Save assistant response to session
    if assistant_content:
        assistant_message = ChatMessage(
            role="assistant",
            content=assistant_content,
            timestamp=datetime.now(timezone.utc)
        )
        session.messages.append(assistant_message)
        save_session(session)


async def workflow_stream_generator(
    request: ChatRequest, session: SessionHistory, user: User
) -> AsyncGenerator[str, None]:
    """
    Generate SSE stream for workflow execution.

    Args:
        request: Chat request with workflow_id
        session: Current chat session
        user: Current authenticated user

    Yields:
        SSE event strings for workflow execution progress
    """
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

    try:
        async with asyncio.timeout(WORKFLOW_TIMEOUT):
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
                        timestamp=datetime.now(timezone.utc)
                    )
                    session.messages.append(assistant_message)
                    save_session(session)
                    yield format_sse_event("done", {
                        "status": "success",
                        "message": "Workflow completed"
                    })
                    return
    except TimeoutError:
        logger.warning("Workflow execution timed out after %ds", WORKFLOW_TIMEOUT)
        yield format_sse_event("error", {"message": f"Workflow execution timed out ({WORKFLOW_TIMEOUT}s)"})
        yield format_sse_event("done", {"status": "error", "message": "Timeout"})
