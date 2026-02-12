"""
Skill Pydantic Models

Data models for the Skill system compatible with Agent Skills specification.
"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SkillInput(BaseModel):
    """Input variable definition for a skill."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Variable name used in prompt templates like {{name}}",
    )
    label: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="UI display label for the input",
    )
    type: Literal["text", "textarea"] = Field(
        default="text",
        description="Input type: text or textarea",
    )
    required: bool = Field(
        default=False,
        description="Whether this input is required",
    )
    default: Optional[str] = Field(
        default=None,
        max_length=1024,
        description="Default value if not provided",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Help text describing the input",
    )


class SkillModelConfig(BaseModel):
    """LLM model configuration for skill execution."""

    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0-2)",
    )
    max_tokens: Optional[int] = Field(
        default=2000,
        ge=1,
        le=8192,
        description="Maximum tokens to generate",
    )


class SkillSummary(BaseModel):
    """Lightweight skill info for list views."""

    name: str = Field(..., description="Skill name (unique identifier)")
    description: str = Field(..., description="Short description of skill purpose")
    inputs: Optional[List[SkillInput]] = Field(
        default=None,
        description="Input variable definitions",
    )
    has_inputs: bool = Field(
        default=False,
        description="Whether skill has defined inputs",
    )
    has_knowledge_base: bool = Field(
        default=False,
        description="Whether skill has associated knowledge base",
    )
    updated_at: datetime = Field(..., description="Last modification timestamp")

    model_config = ConfigDict(from_attributes=True)


class SkillDetail(BaseModel):
    """Complete skill information including prompt content."""

    # Standard fields (Agent Skills spec)
    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Skill name (unique, lowercase, alphanumeric + hyphens)",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="Description of skill functionality and use cases",
    )
    license: Optional[str] = Field(
        default=None,
        max_length=64,
        description="License name (e.g., MIT)",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Arbitrary metadata key-value pairs",
    )

    # Extension fields (Agent Flow Lite specific)
    inputs: Optional[List[SkillInput]] = Field(
        default=None,
        description="Input variable definitions",
    )
    knowledge_base: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Associated knowledge base ID or name",
    )
    model: Optional[SkillModelConfig] = Field(
        default=None,
        description="Model configuration for execution",
    )
    user_id: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Owner user ID (reserved for future use)",
    )

    # Content fields
    prompt: str = Field(
        ...,
        description="Markdown body (the prompt template)",
    )
    raw_content: str = Field(
        ...,
        description="Complete SKILL.md file content",
    )

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)

    @property
    def has_inputs(self) -> bool:
        return bool(self.inputs)

    @property
    def has_knowledge_base(self) -> bool:
        return bool(self.knowledge_base)


class SkillCreateRequest(BaseModel):
    """Request model for creating a new skill."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Skill name (will be used as folder name)",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Complete SKILL.md file content",
    )

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Validate skill name format."""
        import re

        # Must be lowercase
        if v != v.lower():
            raise ValueError("Skill name must be lowercase")

        # Must match pattern: lowercase letters, numbers, hyphens only
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Skill name can only contain lowercase letters, numbers, and hyphens"
            )

        # Cannot start or end with hyphen
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Skill name cannot start or end with a hyphen")

        # No consecutive hyphens
        if "--" in v:
            raise ValueError("Skill name cannot contain consecutive hyphens")

        return v


class SkillUpdateRequest(BaseModel):
    """Request model for updating an existing skill."""

    content: str = Field(
        ...,
        min_length=1,
        description="Complete SKILL.md file content (name cannot be changed)",
    )


class SkillRunRequest(BaseModel):
    """Request model for executing a skill."""

    inputs: Dict[str, str] = Field(
        default_factory=dict,
        description="Input variable values (name -> value)",
    )


class SkillListResponse(BaseModel):
    """Response model for skill list endpoint."""

    skills: List[SkillSummary]
    total: int


class SkillValidationError(BaseModel):
    """Validation error details for skill operations."""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Human-readable error message")
    code: Optional[str] = Field(default=None, description="Error code for i18n")
