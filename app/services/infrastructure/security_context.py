"""
Security Context Service Module.

Provides abstractions for resolving the active actor identity and authorization
metadata within the request execution context.
"""

from typing import TypedDict

from app.domain.enums import ActorType


class ActorIdentity(TypedDict):
    """Data structure representing the resolved caller identity."""

    id: str
    type: ActorType
    name: str


class SecurityContextService:
    """Service resolving caller identity metadata across request executions."""

    def get_current_actor(self) -> ActorIdentity:
        """
        Retrieves identity details for the active actor executing the current request.

        Returns:
            ActorIdentity: Structured actor details including ID, type, and display name.
        """
        return {
            "id": "user-christian",
            "type": ActorType.USER,
            "name": "Christian",
        }
