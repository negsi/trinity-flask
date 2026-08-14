"""
LLM Execution Repository Protocol Module.

Defines the domain repository interface for persisting and retrieving
LLM execution records and task chain metadata.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.llm_execution import LLMExecution


class LLMExecutionRepository(ABC):
    """Abstract interface for LLMExecution domain persistence."""

    @abstractmethod
    def save(self, execution: LLMExecution) -> LLMExecution:
        """
        Persists or updates an LLMExecution record.

        Args:
            execution (LLMExecution): Entity to save.

        Returns:
            LLMExecution: The saved entity instance.
        """
        pass

    @abstractmethod
    def get_by_id(self, execution_id: str) -> Optional[LLMExecution]:
        """
        Retrieves an LLMExecution by its unique identifier.

        Args:
            execution_id (str): Unique identifier.

        Returns:
            Optional[LLMExecution]: The entity if found, else None.
        """
        pass

    @abstractmethod
    def get_by_message_id(self, message_id: str) -> List[LLMExecution]:
        """
        Retrieves all LLMExecutions associated with a specific message ID.

        Args:
            message_id (str): Associated message ID.

        Returns:
            List[LLMExecution]: List of matching executions.
        """
        pass

    @abstractmethod
    def get_by_conversation_id(self, conversation_id: str) -> List[LLMExecution]:
        """
        Retrieves all LLMExecutions associated with a conversation.

        Args:
            conversation_id (str): Target conversation ID.

        Returns:
            List[LLMExecution]: List of matching executions.
        """
        pass