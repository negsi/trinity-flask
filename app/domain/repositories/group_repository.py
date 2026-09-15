"""Group Repository Interface Module."""

from abc import ABC, abstractmethod
from app.domain.models.group import Group


class GroupRepository(ABC):
    """Abstract Base Class for Group persistence."""

    @abstractmethod
    def save(self, group: Group) -> Group:
        pass

    @abstractmethod
    def get_by_id(self, group_id: str) -> Group | None:
        pass

    @abstractmethod
    def get_all(self) -> list[Group]:
        pass

    @abstractmethod
    def delete(self, group_id: str) -> bool:
        pass