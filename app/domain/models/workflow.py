"""Workflow domain model definitions."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

from app.domain.errors import ValidationError


@dataclass(slots=True)
class WorkflowNode:
    """Domain model representing a single agent node within a workflow graph."""

    agent_id: str
    agent_name: str
    x: float = 0.0
    y: float = 0.0
    prompt: str = ""
    agent_description: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValidationError("Workflow node ID cannot be empty.")
        if not self.agent_id or not self.agent_id.strip():
            raise ValidationError("Workflow node agent_id cannot be empty.")
        if not self.agent_name or not self.agent_name.strip():
            raise ValidationError("Workflow node agent_name cannot be empty.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agentId": self.agent_id,
            "agentName": self.agent_name,
            "agentDescription": self.agent_description or "",
            "x": self.x,
            "y": self.y,
            "prompt": self.prompt,
        }


@dataclass(slots=True)
class WorkflowEdge:
    """Domain model representing a directed connection between two workflow nodes."""

    source_node_id: str
    target_node_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValidationError("Workflow edge ID cannot be empty.")
        if not self.source_node_id or not self.source_node_id.strip():
            raise ValidationError("Workflow edge source_node_id cannot be empty.")
        if not self.target_node_id or not self.target_node_id.strip():
            raise ValidationError("Workflow edge target_node_id cannot be empty.")
        if self.source_node_id == self.target_node_id:
            raise ValidationError("A workflow node cannot be connected to itself.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sourceNodeId": self.source_node_id,
            "targetNodeId": self.target_node_id,
        }


@dataclass(slots=True)
class Workflow:
    """Domain model representing a multi-agent workflow graph."""

    name: str
    description: str | None = None
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError("Workflow name cannot be empty.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }