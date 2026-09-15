"""API Request Schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class CreateAgentRequest(BaseModel):
    """Request payload schema for agent creation."""

    name: str = Field(..., min_length=1, max_length=100)
    system_prompt: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    group_ids: List[str] = Field(default_factory=list)

    memory_enabled: bool = False
    memory_mode: str = "user_only"
    memory_limit_type: str = "all"
    memory_message_count: Optional[int] = None


class UpdateAgentRequest(BaseModel):
    """Request payload schema for agent updates (partial or full)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    system_prompt: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    group_ids: Optional[List[str]] = None

    memory_enabled: Optional[bool] = None
    memory_mode: Optional[str] = None
    memory_limit_type: Optional[str] = None
    memory_message_count: Optional[int] = None


class GroupRequest(BaseModel):
    """Request payload schema for group creation and modification."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class SendMessageRequest(BaseModel):
    """Request payload schema for sending a chat message."""

    conversation_id: Optional[str] = Field(None)
    text: str = Field(..., min_length=1)
    recipient_id: Optional[str] = None


class AssignAgentsRequest(BaseModel):
    """Request payload schema for assigning agents to a group."""

    agent_ids: list[str]