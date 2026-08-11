"""
Agent Context Builder Service.

Responsible for assembling complete LLM prompts by combining system instructions,
agent parameters, uploaded knowledge base datasources, and message attachments.
"""

import logging
from pathlib import Path
from typing import List, Optional
import pypdf

from app.domain.llm import LLMMessage
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)

LLM_DIR = Path(__file__).resolve().parent / "llm"
BASE_PROMPT_PATH = LLM_DIR / "base_agent.prompt.md"
RESPONSE_FORMAT_PATH = LLM_DIR / "base_agent.response_format.md"


class AgentContextBuilder:
    """Service that compiles prompt components into LLM context structures."""

    def __init__(self, agent_service: AgentService):
        self.agent_service = agent_service

    def build_llm_messages(
        self,
        user_text: str,
        agent_id: Optional[str],
        attachments: Optional[List[object]] = None,
    ) -> List[LLMMessage]:
        """
        Builds system and user messages for an LLM prompt turn.

        Args:
            user_text (str): Primary user input string.
            agent_id (Optional[str]): Target agent ID for prompt customization.
            attachments (Optional[List[object]]): Optional list of MessageAttachment objects attached to the user message.

        Returns:
            List[LLMMessage]: Constructed list of messages.
        """
        system_prompts: List[str] = []

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

        if agent:
            combined_system_prompt = combined_system_prompt.replace("{agent.name}", agent.name)

        # 1. User-Text aufbauen
        final_user_content = user_text or ""

        # 2. Falls Nachrichten-Anhänge dabei sind, deren Inhalt auslesen und an den User-Text anhängen
        if attachments:
            att_context = self._format_attachments_context(attachments)
            if att_context:
                final_user_content += f"\n\n{att_context}"

        return [
            LLMMessage(role="system", content=combined_system_prompt),
            LLMMessage(role="user", content=final_user_content),
        ]

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