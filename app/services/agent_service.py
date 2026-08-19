"""
Agent Application Service Module.

Encapsulates business operations for agent creation, modification, retrieval, and skill execution.
"""

import logging
from typing import Any

from app.domain.errors import AgentNotFoundError, ToolExecutionError, ToolNotFoundError
from app.domain.models.agent import Agent
from app.domain.repositories.agent_repository import AgentRepository
from app.services.tools import ToolRegistry

logger = logging.getLogger(__name__)


class AgentService:
    """Service managing Agent lifecycle and skill execution."""

    def __init__(
        self,
        agent_repo: AgentRepository,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.agent_repo = agent_repo
        self.tool_registry = tool_registry

    def create_agent(
        self,
        name: str,
        system_prompt: str | None = None,
        description: str | None = None,
        memory_enabled: bool = False,
        memory_mode: str = "user_only",
        memory_limit_type: str = "all",
        memory_message_count: int | None = None,
    ) -> Agent:
        """
        Creates and persists a new Agent entity.

        Args:
            name: Display name.
            system_prompt: Custom system prompt instruction.
            description: Short summary of agent purpose.
            memory_enabled: Whether agent recalls historical chat turns.
            memory_mode: Memory filtering strategy ('user_only', 'full').
            memory_limit_type: Truncation strategy ('all', 'message_count').
            memory_message_count: Number of recent turns to retain.

        Returns:
            Agent: The saved agent model.
        """
        new_agent = Agent(
            name=name,
            system_prompt=system_prompt,
            description=description,
            memory_enabled=memory_enabled,
            memory_mode=memory_mode,
            memory_limit_type=memory_limit_type,
            memory_message_count=memory_message_count,
        )
        saved = self.agent_repo.save(new_agent)
        logger.info("Created Agent '%s' with ID '%s'", saved.name, saved.id)
        return saved

    def update_agent(
        self,
        agent_id: str,
        name: str,
        system_prompt: str,
        description: str | None = None,
        memory_enabled: bool = False,
        memory_mode: str = "user_only",
        memory_limit_type: str = "all",
        memory_message_count: int | None = None,
    ) -> Agent:
        """
        Updates an existing Agent entity.

        Raises:
            AgentNotFoundError: If no agent with the given ID exists.
        """
        agent = self.get_agent(agent_id)

        agent.name = name
        agent.system_prompt = system_prompt
        agent.description = description
        agent.memory_enabled = memory_enabled
        agent.memory_mode = memory_mode
        agent.memory_limit_type = memory_limit_type
        agent.memory_message_count = memory_message_count

        saved = self.agent_repo.save(agent)
        logger.info("Updated Agent '%s' (ID: '%s')", saved.name, saved.id)
        return saved

    def get_agent(self, agent_id: str) -> Agent:
        """
        Retrieves an Agent entity by ID.

        Raises:
            AgentNotFoundError: If the agent cannot be found.
        """
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent with ID '{agent_id}' was not found.")
        return agent

    def get_all_agents(self) -> list[Agent]:
        """Retrieves all registered Agent entities."""
        return self.agent_repo.get_all()

    def delete_agent(self, agent_id: str) -> None:
        """
        Permanently deletes an Agent entity.

        Raises:
            AgentNotFoundError: If the agent does not exist.
        """
        self.get_agent(agent_id)
        self.agent_repo.delete(agent_id)
        logger.info("Deleted Agent with ID '%s'", agent_id)

    def execute_skill(
        self,
        agent_id: str,
        skill_name: str,
        parameters: dict[str, Any],
    ) -> str:
        """
        Executes a registered skill or tool function on behalf of an agent.

        Args:
            agent_id: ID of the requesting agent.
            skill_name: Registered tool identifier.
            parameters: Keyword parameters for tool execution.

        Returns:
            str: Output of the tool execution.

        Raises:
            AgentNotFoundError: If the agent is missing.
            ToolExecutionError: If registry is unconfigured or tool execution fails.
            ToolNotFoundError: If skill name is unmapped.
        """
        self.get_agent(agent_id)

        if not self.tool_registry:
            raise ToolExecutionError("No ToolRegistry is configured on the AgentService.")

        available_tools = self.tool_registry.get_tools()
        if skill_name not in available_tools:
            raise ToolNotFoundError(f"No execution tool registered with name '{skill_name}'.")

        tool_func = available_tools[skill_name]
        try:
            return str(tool_func(**parameters))
        except Exception as exc:
            logger.error("Error executing skill '%s' for agent '%s': %s", skill_name, agent_id, exc, exc_info=True)
            raise ToolExecutionError(f"Error executing skill '{skill_name}': {exc}") from exc
