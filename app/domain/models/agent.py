from dataclasses import dataclass, field
from typing import List, Optional
from app.domain.errors import ValidationError
from app.domain.models.datasource import Datasource

@dataclass
class Agent:
    """Domain model representing an AI agent instance."""
    name: str
    system_prompt: str = None
    description: Optional[str] = None
    datasources: List[Datasource] = field(default_factory=list)
    
    memory_enabled: bool = False
    memory_mode: str = "user_only"
    memory_limit_type: str = "all"
    memory_message_count: Optional[int] = None
    
    id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "memory_enabled": self.memory_enabled,
            "memory_mode": self.memory_mode,
            "memory_limit_type": self.memory_limit_type,
            "memory_message_count": self.memory_message_count,
            "datasources": [ds.to_dict() for ds in self.datasources]
        }

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValidationError("NAME_REQUIRED")
        
        # Validierung der Memory-Settings (Strings an Frontend/DTO angepasst)
        if self.memory_mode not in ("user_only", "all"):
            raise ValidationError("INVALID_MEMORY_MODE")
        if self.memory_limit_type not in ("all", "message_count"):
            raise ValidationError("INVALID_MEMORY_LIMIT_TYPE")
        if self.memory_limit_type == "message_count" and (not self.memory_message_count or self.memory_message_count <= 0):
            raise ValidationError("MEMORY_MESSAGE_COUNT_REQUIRED")