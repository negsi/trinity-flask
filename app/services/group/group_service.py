"""Group Application Service Module."""

import logging
from app.domain.errors import ValidationError
from app.domain.models.group import Group
from app.domain.repositories.group_repository import GroupRepository
from app.domain.repositories.agent_repository import AgentRepository  

logger = logging.getLogger(__name__)


class GroupService:
    """Service managing Group lifecycle."""

    def __init__(self, group_repo: GroupRepository, agent_repo: AgentRepository) -> None:
        self.group_repo = group_repo
        self.agent_repo = agent_repo  

    def create_group(self, name: str, description: str | None = None) -> Group:
        new_group = Group(name=name, description=description)
        saved = self.group_repo.save(new_group)
        logger.info("Created Group '%s' with ID '%s'", saved.name, saved.id)
        return saved

    def update_group(self, group_id: str, name: str, description: str | None = None) -> Group:
        group = self.get_group(group_id)
        group.name = name
        group.description = description
        saved = self.group_repo.save(group)
        logger.info("Updated Group '%s' (ID: '%s')", saved.name, saved.id)
        return saved

    def update_group_agents(self, group_id: str, agent_ids: list[str]) -> None:
        """Updates the agent assignments for a specific group."""
        self.get_group(group_id) 
        
        self.agent_repo.update_group_assignments(group_id=group_id, agent_ids=agent_ids)
        logger.info("Updated agent assignments for Group ID '%s' (Count: %d)", group_id, len(agent_ids))

    def get_group(self, group_id: str) -> Group:
        group = self.group_repo.get_by_id(group_id)
        if not group:
            raise ValidationError(f"Group with ID '{group_id}' was not found.")
        return group

    def get_all_groups(self) -> list[Group]:
        return self.group_repo.get_all()

    def delete_group(self, group_id: str) -> None:
        self.get_group(group_id)
        self.group_repo.delete(group_id)
        logger.info("Deleted Group with ID '%s'", group_id)