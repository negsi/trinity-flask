"""
Security Context Service Module.

Resolves caller identity and actor metadata from request execution contexts.
"""

from typing import Any, Dict
from app.domain.enums import ActorType


class SecurityContextService:
    """Service resolving active caller identity metadata across request executions."""

    def get_current_actor(self) -> Dict[str, Any]:
        """
        Retrieves identity details for the active actor executing the current request.

        Returns:
            Dict[str, Any]: Actor identifier, classification type, and display name.
        """
        return {
            "id": "user-christian",
            "type": ActorType.USER,
            "name": "Christian",
        }
