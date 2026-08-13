"""
Agent Context Builder Service.

Responsible for assembling complete LLM prompts by combining system instructions,
agent parameters, memory configuration, uploaded knowledge base datasources, and message attachments.
"""

import logging
from pathlib import Path
from typing import List, Optional
import pypdf
from datetime import datetime, timezone

from app.domain.llm import LLMMessage
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)

LLM_DIR = Path(__file__).resolve().parent / "llm"
BASE_PROMPT_PATH = LLM_DIR / "base_agent.prompt.md"
RESPONSE_FORMAT_PATH = LLM_DIR / "base_agent.response_format.md"


class AgentContextBuilder:
    """Service that compiles prompt components into LLM context structures."""

    def __init__(
        self, 
        agent_service: AgentService, 
        message_repository: Optional[object] = None
    ):
        self.agent_service = agent_service
        self.message_repository = message_repository

    def build_llm_messages(
        self,
        user_text: str,
        agent_id: Optional[str],
        conversation_id: Optional[str] = None,
        attachments: Optional[List[object]] = None,
        conversation_history: Optional[List[object]] = None,
    ) -> List[LLMMessage]:
        """
        Builds system, historical context, and user messages for an LLM prompt turn.

        Args:
            user_text (str): Primary user input string.
            agent_id (Optional[str]): Target agent ID for prompt customization.
            conversation_id (Optional[str]): Conversation ID to fetch history from DB if not explicitly passed.
            attachments (Optional[List[object]]): Optional list of MessageAttachment objects attached to current user message.
            conversation_history (Optional[List[object]]): Optional explicit list of past Message objects.

        Returns:
            List[LLMMessage]: Constructed list of messages including system instructions and filtered memory history.
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
                logger.error(
                    f"Error loading agent prompt context for '{agent_id}': {e}",
                    exc_info=True,
                )

        combined_system_prompt = "\n\n---\n\n".join(system_prompts)

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        combined_system_prompt = combined_system_prompt.replace("{date.time}", now_str)

        if agent:
            combined_system_prompt = combined_system_prompt.replace("{agent.name}", agent.name)

        messages: List[LLMMessage] = [
            LLMMessage(role="system", content=combined_system_prompt)
        ]

        # 1. Gedächtnis / Conversation History einbinden (falls beim Agenten aktiviert)
        if agent and getattr(agent, "memory_enabled", False):
            # Falls keine History übergeben wurde, versuchen wir sie über die DB zu holen
            if conversation_history is None and conversation_id and self.message_repository:
                try:
                    conversation_history = self.message_repository.get_by_conversation_id(conversation_id)
                except Exception as e:
                    logger.error(
                        f"Error fetching conversation history for conversation_id '{conversation_id}': {e}",
                        exc_info=True,
                    )

            if conversation_history:
                history_messages = self._build_agent_context_history(agent, conversation_history)
                messages.extend(history_messages)

        # 2. Aktuellen User-Text aufbauen
        final_user_content = user_text or ""

        # 3. Falls Nachrichten-Anhänge dabei sind, deren Inhalt auslesen und an den User-Text anhängen
        if attachments:
            att_context = self._format_attachments_context(attachments)
            if att_context:
                final_user_content += f"\n\n{att_context}"

        messages.append(LLMMessage(role="user", content=final_user_content))

        return messages

    def _build_agent_context_history(self, agent, conversation_messages: list) -> List[LLMMessage]:
        """Filtert den bisherigen Chat-Verlauf basierend auf den Memory-Einstellungen des Agenten."""
        history = conversation_messages.copy()

        if getattr(agent, "memory_mode", "user_only") == "user_only":
            history = [
                msg for msg in history 
                if getattr(msg, "sender_type", None) == "user" 
                or getattr(getattr(msg, "sender_type", None), "value", None) == "user"
            ]

        if getattr(agent, "memory_limit_type", "all") == "message_count" and getattr(agent, "memory_message_count", None):
            limit = agent.memory_message_count
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
        """Loads and formats the base agent instruction prompt."""
        try:
            if BASE_PROMPT_PATH.exists():
                content = BASE_PROMPT_PATH.read_text(encoding="utf-8")
                response_format = self._load_response_format()
                return content.replace(
                    "{base_agent.response_format.md}", response_format
                ).strip()
        except Exception as e:
            logger.error(f"Error loading base prompt ({BASE_PROMPT_PATH}): {e}")
        return ""

    def _load_response_format(self) -> str:
        """Loads response format template instructions."""
        try:
            if RESPONSE_FORMAT_PATH.exists():
                return RESPONSE_FORMAT_PATH.read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.error(f"Error loading response format ({RESPONSE_FORMAT_PATH}): {e}")
        return ""

    def _format_datasources_context(self, datasources: list) -> str:
        """Formats attached knowledge datasources into text context blocks."""
        if not datasources:
            return ""

        context_blocks = ["### KNOWLEDGE_BASE:"]
        for ds in datasources:
            filename = getattr(ds, "name", None) or getattr(ds, "filename", "Untitled")
            file_path = getattr(ds, "file_path", None)
            mime_type = getattr(ds, "mime_type", "")

            if not file_path:
                continue

            content = self._extract_file_content(file_path, mime_type)
            if content:
                context_blocks.append(
                    f"--- START FILE: {filename} ---\n{content}\n--- END FILE: {filename} ---"
                )

        return "\n\n".join(context_blocks)

    def _format_attachments_context(self, attachments: list) -> str:
        """Formats message attachments into text context blocks for the current turn."""
        if not attachments:
            return ""

        context_blocks = ["### ATTACHED_FILES_IN_THIS_MESSAGE:"]
        for att in attachments:
            filename = (
                getattr(att, "name", None)
                or getattr(att, "filename", None)
                or getattr(att, "original_filename", "Untitled")
            )
            file_path = getattr(att, "file_path", None)
            mime_type = getattr(att, "mime_type", "")

            if not file_path:
                continue

            content = self._extract_file_content(file_path, mime_type)
            if content:
                context_blocks.append(
                    f"--- START ATTACHMENT: {filename} ---\n{content}\n--- END ATTACHMENT: {filename} ---"
                )

        return "\n\n".join(context_blocks)

    def _extract_file_content(self, file_path_str: str, mime_type: str) -> Optional[str]:
        """Extracts text content from local PDF or plain text documents."""
        path = Path(file_path_str)
        if not path.exists():
            logger.warning(f"File does not exist: {file_path_str}")
            return None

        if mime_type == "application/pdf" or path.suffix.lower() == ".pdf":
            try:
                reader = pypdf.PdfReader(path)
                extracted_text = [
                    f"--- Page {idx + 1} ---\n{page.extract_text()}"
                    for idx, page in enumerate(reader.pages)
                    if page.extract_text()
                ]
                return "\n\n".join(extracted_text).strip()
            except Exception as e:
                logger.error(f"Error reading PDF file '{file_path_str}': {e}")
                return None

        try:
            return path.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception as e:
            logger.error(f"Error reading text file '{file_path_str}': {e}")
            return None