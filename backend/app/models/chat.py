"""
Chat API models for request/response handling.
"""
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message."""
    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message role: user, assistant, or system"
    )
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(
        default=None, description="Message timestamp"
    )


class ChatRequest(BaseModel):
    """
    Chat request model for SSE streaming chat endpoint.
    
    - session_id: Unique session identifier
    - message: User's input message
    - user_id: User identifier for memory (optional)
    - workflow_id: Optional workflow to execute (not implemented yet)
    - kb_id: Optional knowledge base ID for RAG-enhanced responses
    """
    session_id: str = Field(
        ..., description="Unique session identifier for conversation continuity"
    )
    message: str = Field(
        ..., description="User's input message", min_length=1
    )
    user_id: Optional[str] = Field(
        default=None, description="User identifier for session memory"
    )
    workflow_id: Optional[str] = Field(
        default=None, description="Optional workflow ID (not implemented yet)"
    )
    kb_id: Optional[str] = Field(
        default=None, description="Optional knowledge base ID for RAG retrieval"
    )


class SessionHistory(BaseModel):
    """Session history model for storing conversation."""
    session_id: str = Field(..., description="Session identifier")
    messages: List[ChatMessage] = Field(
        default_factory=list, description="List of chat messages"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    kb_id: Optional[str] = Field(default=None)
    workflow_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)


class SSEEvent(BaseModel):
    """Base model for SSE events."""
    event: str = Field(..., description="Event type")
    data: dict = Field(default_factory=dict, description="Event data")


class ThoughtEventData(BaseModel):
    """Data for 'thought' event - RAG retrieval process."""
    type: Literal["retrieval"] = "retrieval"
    status: Literal["start", "searching", "complete"] = Field(
        ..., description="Retrieval status"
    )
    kb_id: str = Field(..., description="Knowledge base ID")
    query: str = Field(..., description="Search query")
    results_count: Optional[int] = Field(
        default=None, description="Number of results found"
    )
    top_results: Optional[List[dict]] = Field(
        default=None, description="Top retrieval results"
    )


class TokenEventData(BaseModel):
    """Data for 'token' event - LLM generated token."""
    content: str = Field(..., description="Generated token content")


class CitationEventData(BaseModel):
    """Data for 'citation' event - source metadata."""
    sources: List[dict] = Field(
        ..., description="List of citation sources with doc_id, chunk_index, score"
    )


class DoneEventData(BaseModel):
    """Data for 'done' event - completion marker."""
    status: Literal["success", "error"] = "success"
    message: Optional[str] = Field(
        default=None, description="Optional completion message or error"
    )
