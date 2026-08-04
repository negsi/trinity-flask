from enum import Enum
from app.domain.enums import ActorType


class SecurityContextService:
    """
    Service responsible for determining the current actor (user, agent, or system)
    executing a request within the application context.

    This service abstracts identity retrieval from incoming requests (e.g., Flask `g`, 
    JWT headers, or API tokens), providing a unified interface to fetch caller metadata 
    across domain services and API endpoints.
    """

    def get_current_actor(self) -> dict:
        """
        Retrieves the details of the active actor making the request.

        Currently defaults to a mock human user payload. In production, this method 
        should inspect session state, request headers, or auth tokens to dynamically 
        identify the caller.

        Returns:
            dict: A dictionary containing the actor's unique identifier (`id`), 
                  domain actor classification (`type`), and display name (`name`).
        """
        # Example lookup logic for future implementation:
        # 1. If an agent API token or service header is present:
        # return {
        #     "id": "agent-cypher-uuid",
        #     "type": ActorType.AGENT,
        #     "name": "Cypher"
        # }

        # 2. Standard fallback for the currently authenticated human user:
        return {
            "id": "user-christian",
            "type": ActorType.USER,
            "name": "Christian"
        }