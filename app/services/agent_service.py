"""
Agent Application Service.

Encapsulates business operations for agent creation, modification, retrieval, and tool execution.
"""

from typing import List, Optional
from app.domain.models.agent import Agent
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.errors import NotFoundError
from app.services.tools import SYSTEM_TOOLS


class AgentService:
    """Service class managing agent lifecycle operations."""

    def __init__(self, agent_repo: AgentRepository):
        self.agent_repo = agent_repo

    def create_agent(
        self, 
        name: str, 
        system_prompt: Optional[str] = None, 
        description: Optional[str] = None
    ) -> Agent:
        """Creates and persists a new Agent entity."""
        new_agent = Agent(
            name=name,
            system_prompt=system_prompt,
            description=description
        )

        return self.agent_repo.save(new_agent)

    def update_agent(
        self, 
        agent_id: str, 
        name: str, 
        system_prompt: str, 
        description: Optional[str] = None
    ) -> Agent:
        """Updates existing agent parameters."""
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(f"AGENT_NOT_FOUND: '{agent_id}'")

        agent.name = name
        agent.system_prompt = system_prompt
        agent.description = description

        return self.agent_repo.save(agent)

    def get_agent(self, agent_id: str) -> Agent:
        """Retrieves an agent entity or raises NotFoundError if missing."""
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' was not found.")
        return agent

    def get_all_agents(self) -> List[Agent]:
        """Retrieves all registered agents."""
        return self.agent_repo.get_all()

    def delete_agent(self, agent_id: str) -> None:
        """Permanently deletes an agent entity."""
        self.get_agent(agent_id)
        self.agent_repo.delete(agent_id)

    def execute_skill(self, agent_id: str, skill_name: str, parameters: dict) -> str:
        """Executes a tool from the system registry directly in-process."""
        self.get_agent(agent_id)

        if skill_name not in SYSTEM_TOOLS:
            raise NotFoundError(f"No Python function registered for tool '{skill_name}'.")

        tool_func = SYSTEM_TOOLS[skill_name]

        try:
            return tool_func(**parameters)
        except Exception as e:
            raise RuntimeError(f"Error executing tool '{skill_name}': {str(e)}")
