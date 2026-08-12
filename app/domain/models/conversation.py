from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class Conversation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: Optional[str] = None  # <-- NEU
    title: str = "Neue Konversation"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }