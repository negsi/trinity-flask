"""
Agent Context Builder Service Module.

Assembles prompt components into structured LLM message sequences, incorporating system
instructions, dynamic timestamps, knowledge base files, message attachments, and memory history.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, List, Optional

from app.domain.llm import LLMMessage
from app.services.agent_service import AgentService
from app.services.file_storage_service import FileStorageService

logger = logging.getLogger(__name__)

LLM_DIR = Path(__file__).resolve().parent / "llm"
BASE_PROMPT_PATH = LLM_DIR / "base_agent.prompt.md"
RESPONSE_FORMAT_PATH = LLM_DIR / "base_agent.response_format.md"


class AgentContextBuilder:
    """Service compiling system instructions, memories, and documents into LLM prompts."""

    def __init__(
        self,
        agent_service: AgentService,
        file_storage_service: FileStorageService,
        message_repository: Optional[Any] = None,
    ) -> None:
        self.agent_service = agent_service
        self.file_storage_service = file_storage_service
        self.message_repository = message_repository

    def build_llm_messages(
        self,
        user_text: str,
        agent_id: Optional[str],
        conversation_id: Optional[str] = None,
        attachments: Optional[List[Any]] = None,
        conversation_history: Optional[List[Any]] = None,
    ) -> List[LLMMessage]:
        """
        Constructs the complete sequence of LLM prompt messages.

        Args:
            user_text (str): Incoming user query.
            agent_id (Optional[str]): Target agent identifier.
            conversation_id (Optional[str]): Active conversation ID.
            attachments (Optional[List[Any]]): Message attachments for the current turn.
            conversation_history (Optional[List[Any]]): Historical conversation messages.

        Returns:
            List[LLMMessage]: Formatted list of system, history, and user messages.
        """
        system_prompts: List[str] = []
        agent = None

        base_prompt = self._load_base_prompt()
        if base_prompt:
            system_prompts.append(base_prompt)

        if agent_id:
            try:
                agent = self.agent_service.get_agent(agent_id)
                if agent:
                    if agent.system_prompt and agent.system_prompt.strip():
                        system_prompts.append(agent.system_prompt.strip())

                    datasources = getattr(agent, "datasources", [])
                    if datasources:
                        ds_context = self._format_datasources_context(datasources)
                        if ds_context:
                            system_prompts.append(ds_context)
            except Exception as e:
                logger.error("Error loading agent context for agent '%s': %s", agent_id, e, exc_info=True)

        combined_system_prompt = "\n\n---\n\n".join(system_prompts)
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        combined_system_prompt = combined_system_prompt.replace("{date.time}", now_str)

        if agent:
            combined_system_prompt = combined_system_prompt.replace("{agent.name}", agent.name)

        messages: List[LLMMessage] = [
            LLMMessage(role="system", content=combined_system_prompt)
        ]

        # 1. Integrate conversation memory based on agent settings
        if agent and getattr(agent, "memory_enabled", False):
            if conversation_history is None and conversation_id and self.message_repository:
                try:
                    conversation_history = self.message_repository.get_by_conversation(conversation_id)
                except Exception as e:
                    logger.error("Error fetching history for conversation '%s': %s", conversation_id, e, exc_info=True)

            if conversation_history:
                messages.extend(self._build_agent_context_history(agent, conversation_history))

        # 2. Build current user turn message
        final_user_content = user_text or ""
        if attachments:
            att_context = self._format_attachments_context(attachments)
            if att_context:
                final_user_content = f"{final_user_content}\n\n{att_context}".strip()

        messages.append(LLMMessage(role="user", content=final_user_content))
        return messages

    def _build_agent_context_history(self, agent: Any, conversation_messages: List[Any]) -> List[LLMMessage]:
        """Filters historical conversation messages according to agent memory rules."""
        history = list(conversation_messages)

        if getattr(agent, "memory_mode", "user_only") == "user_only":
            history = [
                msg for msg in history
                if getattr(msg, "sender_type", None) == "user"
                or getattr(getattr(msg, "sender_type", None), "value", None) == "user"
            ]

        if getattr(agent, "memory_limit_type", "all") == "message_count":
            limit = getattr(agent, "memory_message_count", None)
            if limit and limit > 0:
                history = history[-limit:]

        llm_history: List[LLMMessage] = []
        for msg in history:
            s_type = getattr(msg, "sender_type", "user")
            s_type_val = getattr(s_type, "value", str(s_type))
            role = "user" if s_type_val == "user" else "assistant"
            content = getattr(msg, "text", "") or ""

            if content.strip():
                llm_history.append(LLMMessage(role=role, content=content))

        return llm_history

    def _load_base_prompt(self) -> str:
        """Loads and formats the base agent prompt template."""
        try:
            if BASE_PROMPT_PATH.exists():
                content = BASE_PROMPT_PATH.read_text(encoding="utf-8")
                response_format = self._load_response_format()
                return content.replace("{base_agent.response_format.md}", response_format).strip()
        except Exception as e:
            logger.error("Error reading base prompt file: %s", e)
        return ""

    def _load_response_format(self) -> str:
        """Loads the structured response format template."""
        try:
            if RESPONSE_FORMAT_PATH.exists():
                return RESPONSE_FORMAT_PATH.read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.error("Error reading response format template: %s", e)
        return ""

    def _format_datasources_context(self, datasources: List[Any]) -> str:
        """Extracts and formats knowledge base datasource text."""
        if not datasources:
            return ""

        context_blocks = ["### KNOWLEDGE_BASE:"]
        for ds in datasources:
            filename = getattr(ds, "name", None) or getattr(ds, "filename", "Untitled")
            file_path = getattr(ds, "file_path", None)
            mime_type = getattr(ds, "mime_type", "")

            if not file_path:
                continue

            content = self.file_storage_service.extract_text_content(file_path, mime_type)
            if content:
                context_blocks.append(
                    f"--- START FILE: {filename} ---\n{content}\n--- END FILE: {filename} ---"
                )

        return "\n\n".join(context_blocks)

    def _format_attachments_context(self, attachments: List[Any]) -> str:
        """Extracts and formats message attachment text for the prompt."""
        if not attachments:
            return ""

        context_blocks = ["### ATTACHED_FILES_IN_THIS_MESSAGE:"]
        for att in attachments:
            filename = (
                getattr(att, "name", None)
                or getattr(att, "filename", None)
                or "Untitled"
            )
            file_path = getattr(att, "file_path", None)
            mime_type = getattr(att, "mime_type", "")

            if not file_path:
                continue

            content = self.file_storage_service.extract_text_content(file_path, mime_type)
            if content:
                context_blocks.append(
                    f"--- START ATTACHMENT: {filename} ---\n{content}\n--- END ATTACHMENT: {filename} ---"
                )

        return "\n\n".join(context_blocks)
