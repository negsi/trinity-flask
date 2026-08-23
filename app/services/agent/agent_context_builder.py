"""
Agent Context Builder Service Module.

Assembles prompt components into structured LLM message sequences, incorporating system
instructions, dynamic timestamps, knowledge base files, message attachments, memory history,
and available system agents.
"""

from datetime import datetime, timezone
import logging
import os
from pathlib import Path
from typing import Any

from app.domain.enums import ActorType
from app.domain.llm import LLMMessage
from app.domain.models.agent import Agent
from app.domain.models.datasource import Datasource
from app.domain.models.message import Message, MessageAttachment
from app.domain.repositories.message_repository import MessageRepository
from app.services.agent.agent_service import AgentService
from app.services.infrastructure.file_storage_service import FileStorageService

logger = logging.getLogger(__name__)

LLM_DIR = Path(__file__).resolve().parents[1] / "llm"
BASE_PROMPT_PATH = LLM_DIR / "base_agent.prompt.md"
RESPONSE_FORMAT_PATH = LLM_DIR / "base_agent.response_format.md"


class AgentContextBuilder:
    """Service compiling system instructions, memories, and documents into LLM prompts."""

    def __init__(
        self,
        agent_service: AgentService,
        file_storage_service: FileStorageService,
        message_repository: MessageRepository | None = None,
        conversation_directory: str | None = None,
    ) -> None:
        self.agent_service = agent_service
        self.file_storage_service = file_storage_service
        self.message_repository = message_repository
        self.conversation_directory = conversation_directory

    def build_llm_messages(
        self,
        user_text: str,
        agent_id: str | None,
        conversation_id: str | None = None,
        attachments: list[MessageAttachment] | None = None,
        conversation_history: list[Message] | None = None,
    ) -> list[LLMMessage]:
        """
        Constructs the complete sequence of LLM prompt messages.

        Args:
            user_text: Incoming user query.
            agent_id: Target agent identifier.
            conversation_id: Active conversation ID.
            attachments: Message attachments for the current turn.
            conversation_history: Historical conversation messages.

        Returns:
            list[LLMMessage]: Formatted list of system, history, and user messages.
        """
        system_prompts: list[str] = []
        agent: Agent | None = None

        if base_prompt := self._load_base_prompt():
            system_prompts.append(base_prompt)

        if agent_id:
            try:
                agent = self.agent_service.get_agent(agent_id)
                if agent.system_prompt and agent.system_prompt.strip():
                    system_prompts.append(agent.system_prompt.strip())

                if agent.datasources:
                    ds_context = self._format_datasources_context(agent.datasources)
                    if ds_context:
                        system_prompts.append(ds_context)
            except Exception as exc:
                logger.error("Error loading agent context for agent '%s': %s", agent_id, exc, exc_info=True)

        combined_system = "\n\n---\n\n".join(system_prompts)
        rendered_system = self._render_system_prompt_placeholders(
            template=combined_system,
            agent=agent,
            conversation_id=conversation_id,
        )

        messages: list[LLMMessage] = [LLMMessage(role="system", content=rendered_system)]

        # 1. Integrate conversation memory
        if agent and agent.memory_enabled:
            resolved_history = conversation_history
            if resolved_history is None and conversation_id and self.message_repository:
                try:
                    resolved_history = self.message_repository.get_by_conversation(conversation_id)
                except Exception as exc:
                    logger.error("Error fetching history for conversation '%s': %s", conversation_id, exc)

            if resolved_history:
                messages.extend(self._build_agent_context_history(agent, resolved_history))

        # 2. Build user turn payload
        user_content = self._build_user_message_content(user_text, attachments or [])
        messages.append(LLMMessage(role="user", content=user_content))

        return messages

    def _render_system_prompt_placeholders(
        self,
        template: str,
        agent: Agent | None,
        conversation_id: str | None,
    ) -> str:
        """Substitutes template variables using a structured placeholder mapping."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        conv_id_str = str(conversation_id) if conversation_id else ""
        conv_dir = (
            os.path.join(self.conversation_directory, conv_id_str)
            if self.conversation_directory and conv_id_str
            else ""
        )

        placeholders: dict[str, str] = {
            "{date.time}": now_str,
            "{agent.name}": agent.name if agent else "",
            "{agent.id}": str(agent.id) if agent else "",
            "{conversation.id}": conv_id_str,
            "{conversation.directory}": conv_dir,
            "{available_agents_list}": self._build_available_agents_context(),
        }

        rendered = template
        for placeholder, replacement in placeholders.items():
            rendered = rendered.replace(placeholder, replacement)

        return rendered

    def _build_available_agents_context(self) -> str:
        """Retrieves and formats all active agents in the system into a prompt summary."""
        try:
            agents = self.agent_service.get_all_agents()
            if not agents:
                return "Keine weiteren Agenten im System vorhanden."

            return "\n".join(f'- Agent "{a.name}" (ID: `{a.id}`)' for a in agents)
        except Exception as exc:
            logger.error("Error building available agents context: %s", exc)
            return "Fehler beim Laden der System-Agenten."

    def _build_user_message_content(
        self,
        user_text: str,
        attachments: list[MessageAttachment],
    ) -> str | list[dict[str, Any] | str]:
        """Processes and formats text and media attachments into a provider payload."""
        if not attachments:
            return user_text or ""

        text_attachment_blocks: list[str] = []
        image_parts: list[dict[str, Any]] = []

        for att in attachments:
            file_path = att.file_path
            mime_type = att.mime_type or ""
            filename = att.filename or att.name or "Untitled"

            if not file_path or not Path(file_path).is_file():
                continue

            if mime_type.startswith("image/"):
                try:
                    img_bytes = Path(file_path).read_bytes()
                    image_parts.append({
                        "type": "image",
                        "mime_type": mime_type,
                        "data": img_bytes,
                        "filename": filename,
                    })
                except OSError as exc:
                    logger.error("Failed to read image attachment '%s': %s", file_path, exc)
            else:
                content = self.file_storage_service.extract_text_content(file_path, mime_type)
                if content:
                    text_attachment_blocks.append(
                        f"--- START ATTACHMENT: {filename} ---\n{content}\n--- END ATTACHMENT: {filename} ---"
                    )

        final_text = user_text or ""
        if text_attachment_blocks:
            attached_str = "### ATTACHED_FILES_IN_THIS_MESSAGE:\n" + "\n\n".join(text_attachment_blocks)
            final_text = f"{final_text}\n\n{attached_str}".strip()

        if image_parts:
            payload: list[dict[str, Any] | str] = [final_text] if final_text else []
            payload.extend(image_parts)
            return payload

        return final_text

    def _build_agent_context_history(
        self,
        agent: Agent,
        conversation_messages: list[Message],
    ) -> list[LLMMessage]:
        """Filters and maps historical conversation messages based on agent memory settings."""
        history = list(conversation_messages)

        if agent.memory_mode == "user_only":
            history = [
                msg for msg in history
                if msg.sender_type == ActorType.USER or str(msg.sender_type).lower() == "user"
            ]

        if agent.memory_limit_type == "message_count":
            limit = agent.memory_message_count
            if limit and limit > 0:
                history = history[-limit:]

        llm_history: list[LLMMessage] = []
        for msg in history:
            is_user = msg.sender_type == ActorType.USER or str(msg.sender_type).lower() == "user"
            role = "user" if is_user else "assistant"
            content = msg.text or ""

            if content.strip():
                llm_history.append(LLMMessage(role=role, content=content))

        return llm_history

    def _load_base_prompt(self) -> str:
        """Loads and formats the base agent prompt template."""
        if not BASE_PROMPT_PATH.is_file():
            return ""

        try:
            content = BASE_PROMPT_PATH.read_text(encoding="utf-8")
            response_format = self._load_response_format()
            return content.replace("{base_agent.response_format.md}", response_format).strip()
        except OSError as exc:
            logger.error("Error reading base prompt file: %s", exc)
            return ""

    def _load_response_format(self) -> str:
        """Loads the response format specification."""
        if not RESPONSE_FORMAT_PATH.is_file():
            return ""

        try:
            return RESPONSE_FORMAT_PATH.read_text(encoding="utf-8").strip()
        except OSError as exc:
            logger.error("Error reading response format template: %s", exc)
            return ""

    def _format_datasources_context(self, datasources: list[Datasource]) -> str:
        """Extracts and formats text from knowledge base datasources."""
        if not datasources:
            return ""

        context_blocks = ["### KNOWLEDGE_BASE:"]
        for ds in datasources:
            filename = ds.name or ds.filename or "Untitled"
            file_path = ds.file_path
            mime_type = ds.mime_type or ""

            if not file_path:
                continue

            content = self.file_storage_service.extract_text_content(file_path, mime_type)
            if content:
                context_blocks.append(
                    f"--- START FILE: {filename} ---\n{content}\n--- END FILE: {filename} ---"
                )

        if len(context_blocks) <= 1:
            return ""

        return "\n\n".join(context_blocks)
