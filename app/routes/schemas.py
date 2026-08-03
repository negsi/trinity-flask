"""
API Request Schemas.

Pydantic validation schemas for incoming HTTP API request payloads.
"""

from typing import Optional
from pydantic import BaseModel, Field


class CreateAgentRequest(BaseModel):
    """Request payload schema for agent creation and modification."""
    name: str = Field(..., min_length=1, max_length=100)
    system_prompt: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)


class SendMessageRequest(BaseModel):
    """Request payload schema for sending a chat message."""
    conversation_id: Optional[str] = Field(None)
    sender_id: str = Field(..., min_length=1)
    sender_type: str = Field(..., pattern="^(user|agent|system)$")
    sender_name: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    recipient_id: Optional[str] = None
