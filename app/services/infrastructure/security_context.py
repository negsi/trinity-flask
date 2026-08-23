"""
Security Context Service Module.

Provides abstractions for resolving the active actor identity and authorization
metadata within the request execution context.
"""

from typing import TypedDict
from flask import request, g
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
        # 1. Auf explicit gesetzten Context in flask.g prüfen (z. B. durch Middleware/Service)
        if hasattr(g, "actor") and g.actor:
            return g.actor

        # 2. Prüfen, ob der HTTP-Request ein Sender-Payload für Agent-to-Agent Kommunikation enthält
        if request and request.is_json:
            try:
                data = request.get_json(silent=True) or {}
                sender_id = data.get("sender_id")
                sender_type = data.get("sender_type")

                if sender_type == "agent" or (sender_type == ActorType.AGENT.value):
                    return {
                        "id": sender_id or "agent-system",
                        "type": ActorType.AGENT,
                        "name": data.get("sender_name", f"Agent ({sender_id})"),
                    }
            except Exception:
                pass

        # 3. Standard Fallback: Christian (User)
        return {
            "id": "user-christian",
            "type": ActorType.USER,
            "name": "Christian",
        }