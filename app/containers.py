"""
Dependency Injection Container Module.

Configures application repositories, domain services, context builders,
storage services, tool registries, and system orchestrators.
"""

from dependency_injector import containers, providers

from app.repositories import (
    SQLAlchemyAgentRepository,
    SQLAlchemyConversationRepository,
    SQLAlchemyDatasourceRepository,
    SQLAlchemyLLMExecutionRepository,
    SQLAlchemyMessageRepository,
)
from app.services.agent_context_builder import AgentContextBuilder
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.agent_service import AgentService
from app.services.datasource_service import DatasourceService
from app.services.email_service import EmailService
from app.services.file_storage_service import FileStorageService
from app.services.llm_service import LLMService
from app.services.message_attachment_service import MessageAttachmentService
from app.services.messaging_service import MessagingService
from app.services.react_loop_runner import ReActLoopRunner
from app.services.security_context import SecurityContextService
from app.services.tools import ToolRegistry


class Container(containers.DeclarativeContainer):
    """Declarative dependency injection container managing application service lifecycles."""

    # Application Configuration Provider
    config = providers.Configuration()

    # -------------------------------------------------------------------------
    # Repositories (Data Access Layer)
    # -------------------------------------------------------------------------
    agent_repository = providers.Singleton(
        SQLAlchemyAgentRepository
    )
    datasource_repository = providers.Singleton(
        SQLAlchemyDatasourceRepository
    )
    message_repository = providers.Singleton(
        SQLAlchemyMessageRepository
    )
    conversation_repository = providers.Singleton(
        SQLAlchemyConversationRepository
    )
    llm_execution_repository = providers.Singleton(
        SQLAlchemyLLMExecutionRepository
    )

    # -------------------------------------------------------------------------
    # Infrastructure & Security Services
    # -------------------------------------------------------------------------
    security_context_service = providers.Singleton(
        SecurityContextService
    )

    file_storage_service = providers.Singleton(
        FileStorageService
    )

    email_service = providers.Singleton(
        EmailService,
        server=config.SMTP_SERVER,
        port=config.SMTP_PORT,
        user=config.SMTP_USER,
        password=config.SMTP_PASSWORD,
        sender=config.SMTP_FROM,
    )

    # -------------------------------------------------------------------------
    # Tools & Tool Registry
    # -------------------------------------------------------------------------
    tool_registry = providers.Singleton(
        ToolRegistry,
        file_storage_service=file_storage_service,
        email_service=email_service,
        conversations_folder=config.CONVERSATIONS_FOLDER,
    )

    # -------------------------------------------------------------------------
    # Domain & Application Services
    # -------------------------------------------------------------------------
    agent_service = providers.Factory(
        AgentService,
        agent_repo=agent_repository,
        tool_registry=tool_registry,
    )

    datasource_service = providers.Factory(
        DatasourceService,
        datasource_repo=datasource_repository,
        file_storage_service=file_storage_service,
        upload_folder=config.UPLOAD_FOLDER,
    )

    message_attachment_service = providers.Factory(
        MessageAttachmentService,
        file_storage_service=file_storage_service,
        upload_folder=config.MESSAGE_UPLOAD_FOLDER,
    )

    messaging_service = providers.Factory(
        MessagingService,
        message_repo=message_repository,
        conversation_repo=conversation_repository,
        attachment_service=message_attachment_service,
    )

    llm_service = providers.Factory(
        LLMService,
        default_provider=config.LLM_PROVIDER,
        model_name=config.LLM_MODEL,
    )

    # -------------------------------------------------------------------------
    # Builders, Runners & Orchestrators
    # -------------------------------------------------------------------------
    agent_context_builder = providers.Factory(
        AgentContextBuilder,
        agent_service=agent_service,
        file_storage_service=file_storage_service,
        message_repository=message_repository,
    )

    react_loop_runner = providers.Factory(
        ReActLoopRunner,
        llm_service=llm_service,
        context_builder=agent_context_builder,
        tool_registry=tool_registry,
        email_service=email_service,
    )

    agent_orchestrator = providers.Singleton(
        AgentOrchestrator,
        messaging_service=messaging_service,
        llm_execution_repo=llm_execution_repository,
        react_loop_runner=react_loop_runner,
    )
