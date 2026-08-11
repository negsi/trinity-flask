"""
Dependency Injection Container Module.

Configures application repositories, core domain services, context builders,
and system orchestrators using the dependency_injector framework.
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
from app.services.llm_service import LLMService
from app.services.messaging_service import MessagingService
from app.services.security_context import SecurityContextService
from app.services.message_attachment_service import MessageAttachmentService
from app.services.email_service import EmailService


class Container(containers.DeclarativeContainer):
    """
    Declarative dependency injection container managing application lifetime 
    and service dependency resolution.
    """

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
    # Security & Context Services
    # -------------------------------------------------------------------------
    security_context_service = providers.Singleton(
        SecurityContextService
    )

    # -------------------------------------------------------------------------
    # Domain Services
    # -------------------------------------------------------------------------
    agent_service = providers.Factory(
        AgentService,
        agent_repo=agent_repository,
    )

    datasource_service = providers.Factory(
        DatasourceService,
        datasource_repo=datasource_repository,
        upload_folder=config.UPLOAD_FOLDER,
    )

    message_attachment_service = providers.Factory(
        MessageAttachmentService,
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

    email_service = providers.Singleton(
        EmailService,
        server=config.SMTP_SERVER,
        port=config.SMTP_PORT,
        user=config.SMTP_USER,
        password=config.SMTP_PASSWORD,
        sender=config.SMTP_FROM,
    )

    # -------------------------------------------------------------------------
    # Builders & Orchestrators
    # -------------------------------------------------------------------------
    agent_context_builder = providers.Factory(
        AgentContextBuilder,
        agent_service=agent_service,
    )

    agent_orchestrator = providers.Singleton(
        AgentOrchestrator,
        llm_service=llm_service,
        context_builder=agent_context_builder,
        messaging_service=messaging_service,
        llm_execution_repo=llm_execution_repository,
    )
