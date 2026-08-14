"""LLM Execution Repository Interface Module.

Defines abstract CRUD contracts for persisting LLM task chain and ReAct execution records.
"""

from abc import ABC, abstractmethod

from app.domain.models.llm_execution import LLMExecution


class LLMExecutionRepository(ABC):
    """Abstract Base Class for LLMExecution domain model persistence."""

    @abstractmethod
    def save(self, execution: LLMExecution) -> LLMExecution:
        """Persists or updates an LLMExecution record.

        Args:
            execution (LLMExecution): Entity to persist.

        Returns:
            LLMExecution: The persisted entity instance.

        Raises:
            StorageError: If saving the execution entity fails.
        """
        pass

    @abstractmethod
    def get_by_id(self, execution_id: str) -> LLMExecution | None:
        """Retrieves an execution by its unique ID.

        Args:
            execution_id (str): Unique UUID.

        Returns:
            LLMExecution | None: The execution model if found, else None.

        Raises:
            StorageError: If query execution fails.
        """
        pass

    @abstractmethod
    def get_by_message_id(self, message_id: str) -> list[LLMExecution]:
        """Retrieves all execution records associated with a message ID.

        Args:
            message_id (str): Message UUID.

        Returns:
            list[LLMExecution]: List of matching executions.

        Raises:
            StorageError: If query execution fails.
        """
        pass

    @abstractmethod
    def get_by_conversation_id(self, conversation_id: str) -> list[LLMExecution]:
        """Retrieves all executions associated with a conversation ordered descending by timestamp.

        Args:
            conversation_id (str): Target conversation UUID.

        Returns:
            list[LLMExecution]: List of matching execution records.

        Raises:
            StorageError: If query execution fails.
        """
        pass

    @abstractmethod
    def delete(self, execution_id: str) -> bool:
        """Deletes an execution record by its unique ID.

        Args:
            execution_id (str): Unique UUID.

        Returns:
            bool: True if removed, False if not found.

        Raises:
            StorageError: If deletion fails.
        """
        pass
