"""
Dependency Injection Container Module.

Configures services, repositories, and context builders using the dependency_injector framework.
"""

import os
from dependency_injector import containers, providers

from app.repositories.sqlalchemy_datasource_repository import SQLAlchemyDatasourceRepository
from app.services.agent_service import AgentService
from app.services.datasource_service import DatasourceService
from app.services.messaging_service import MessagingService
from app.services.llm_service import LLMService
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.agent_context_builder import AgentContextBuilder
from app.repositories import (
    SQLAlchemyAgentRepository,
    SQLAlchemyMessageRepository,
    SQLAlchemyConversationRepository,
    SQLAlchemyLLMExecutionRepository
)


class Container(containers.DeclarativeContainer):
    """Declarative dependency injection container for application services and repositories."""

    _CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT = os.path.dirname(_CURRENT_DIR)
    _UPLOAD_PATH = os.path.join(_PROJECT_ROOT, "instance", "uploads")

    config = providers.Configuration()

    # Repositories
    agent_repository = providers.Singleton(SQLAlchemyAgentRepository)
    datasource_repo = providers.Factory(SQLAlchemyDatasourceRepository)
    message_repository = providers.Singleton(SQLAlchemyMessageRepository)
    conversation_repository = providers.Singleton(SQLAlchemyConversationRepository)
    llm_execution_repository = providers.Singleton(SQLAlchemyLLMExecutionRepository)

    # Domain Services
    agent_service = providers.Factory(
        AgentService,
        agent_repo=agent_repository,
    )

    datasource_service = providers.Factory(
        DatasourceService,
        datasource_repo=datasource_repo,
        upload_folder=_UPLOAD_PATH
    )

    messaging_service = providers.Factory(
        MessagingService,
        message_repo=message_repository,
        conversation_repo=conversation_repository
    )

    llm_service = providers.Factory(
        LLMService,
        default_provider=config.LLM_PROVIDER,
        model_name=config.LLM_MODEL
    )

    agent_context_builder = providers.Factory(
        AgentContextBuilder,
        agent_service=agent_service
    )

    agent_orchestrator = providers.Singleton(
        AgentOrchestrator,
        llm_service=llm_service,
        context_builder=agent_context_builder,
        messaging_service=messaging_service,
        llm_execution_repo=llm_execution_repository
    )
