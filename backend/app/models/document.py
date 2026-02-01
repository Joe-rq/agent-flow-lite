"""
Document models for knowledge base.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


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

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Document response model for API."""
    id: str
    kb_id: str
    filename: str
    status: DocumentStatus
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    documents: list[DocumentResponse]
    total: int
