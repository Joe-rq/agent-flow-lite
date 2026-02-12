"""
Document models for knowledge base.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentBase(BaseModel):
    """Base document model with common fields."""
    filename: str = Field(..., description="Original filename")
    status: DocumentStatus = Field(
        default=DocumentStatus.PENDING,
        description="Processing status"
    )


class DocumentCreate(BaseModel):
    """Model for creating a new document."""
    kb_id: str = Field(..., description="Knowledge base ID")


class Document(DocumentBase):
    """Full document model with metadata."""
    id: str = Field(..., description="Document unique ID")
    kb_id: str = Field(..., description="Knowledge base ID")
    file_path: str = Field(..., description="Path to saved file")
    file_size: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    """Document response model for API."""
    id: str
    kb_id: str
    filename: str
    status: DocumentStatus
    file_size: int
    created_at: datetime
    task_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    documents: list[DocumentResponse]
    total: int


class KnowledgeBase(BaseModel):
    """Knowledge base model."""
    id: str = Field(..., description="Knowledge base unique ID")
    name: str = Field(..., description="Knowledge base name")
    document_count: int = Field(default=0, description="Number of documents")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class KnowledgeBaseCreate(BaseModel):
    """Model for creating a new knowledge base."""
    name: str = Field(..., description="Knowledge base name")


class KnowledgeBaseListResponse(BaseModel):
    """Response model for knowledge base list."""
    items: list[KnowledgeBase]
    total: int
