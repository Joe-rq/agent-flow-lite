"""
Workflow Pydantic Models
"""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class GraphData(BaseModel):
    """Vue Flow graph data structure"""

    nodes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Vue Flow nodes"
    )
    edges: List[Dict[str, Any]] = Field(
        default_factory=list, description="Vue Flow edges"
    )


class StartNode(BaseModel):
    id: str = Field(..., min_length=1)
    type: Literal["start"]
    data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class LlmNode(BaseModel):
    id: str = Field(..., min_length=1)
    type: Literal["llm"]
    data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class KnowledgeNode(BaseModel):
    id: str = Field(..., min_length=1)
    type: Literal["knowledge"]
    data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class ConditionNode(BaseModel):
    id: str = Field(..., min_length=1)
    type: Literal["condition"]
    data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class SkillNode(BaseModel):
    id: str = Field(..., min_length=1)
    type: Literal["skill"]
    data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class HttpNode(BaseModel):
    id: str = Field(..., min_length=1)
    type: Literal["http"]
    data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class CodeNode(BaseModel):
    id: str = Field(..., min_length=1)
    type: Literal["code"]
    data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class EndNode(BaseModel):
    id: str = Field(..., min_length=1)
    type: Literal["end"]
    data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


NodeSchema = Annotated[
    Union[
        StartNode,
        LlmNode,
        KnowledgeNode,
        ConditionNode,
        SkillNode,
        HttpNode,
        CodeNode,
        EndNode,
    ],
    Field(discriminator="type"),
]

_NODES_ADAPTER = TypeAdapter(List[NodeSchema])


def parse_workflow_nodes(nodes: List[Dict[str, Any]]) -> List[NodeSchema]:
    return _NODES_ADAPTER.validate_python(nodes)


class WorkflowBase(BaseModel):
    """Base workflow model with common fields"""

    name: str = Field(..., min_length=1, max_length=255, description="Workflow name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Workflow description"
    )
    graph_data: GraphData = Field(
        default_factory=GraphData, description="Vue Flow graph data"
    )


class WorkflowCreate(WorkflowBase):
    """Model for creating a new workflow"""

    pass


class WorkflowUpdate(BaseModel):
    """Model for updating an existing workflow"""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Workflow name"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Workflow description"
    )
    graph_data: Optional[GraphData] = Field(None, description="Vue Flow graph data")


class Workflow(WorkflowBase):
    """Complete workflow model with ID and timestamps"""

    id: str = Field(..., description="Unique workflow identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class WorkflowList(BaseModel):
    """Response model for workflow list"""

    items: List[Workflow]
    total: int
