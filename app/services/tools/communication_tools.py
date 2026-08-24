"""
Communication Tools Module.

Provides email dispatching, LLM delegation, and agent-to-agent messaging routines.
"""

from collections.abc import Callable
import logging
from pathlib import Path
import re
from typing import Any, Generator

from app.services.infrastructure.email_service import EmailService
from app.services.tools.file_tools import get_latest_image_in_dir, locate_file

logger = logging.getLogger(__name__)


def message_llm(message: str, **kwargs: Any) -> str:
    """
    Placeholder tool signature for sub-task delegation.

    Args:
        message: The instruction or message for the LLM.

    Returns:
        str: Echoed message.
    """
    return message


def message_agent(
    target_agent_id: str,
    message: str,
    agent_orchestrator: Any | None = None,
    conversation_id: str | None = None,
    current_agent_id: str | None = None,
    call_depth: int = 1,
    on_event: Callable[[str], None] | None = None,
    base_dir: str | Path | None = None,
    **kwargs: Any,
) -> Generator[str, None, str]:
    if not target_agent_id:
        return "Error: target_agent_id is required."

    if not message or not str(message).strip():
        return "Error: message content cannot be empty."

    if current_agent_id and target_agent_id == current_agent_id:
        return f"Error: Agent '{current_agent_id}' cannot send a message to itself."

    orchestrator = agent_orchestrator() if isinstance(agent_orchestrator, Callable) else agent_orchestrator
    if not orchestrator:
        return "Error: AgentOrchestrator is not configured or available for message_agent."

    resolved_workspace = None
    if base_dir and conversation_id:
        resolved_workspace = str(Path(base_dir).resolve() / str(conversation_id))

    sub_context = {
        "conversation_id": conversation_id,
        "base_dir": base_dir,
        "directory": resolved_workspace,
    }

    try:
        # Delegate live generator stream directly to orchestrator
        res = yield from orchestrator.run_subagent_task_stream(
            target_agent_id=target_agent_id,
            message=message,
            conversation_id=conversation_id,
            caller_agent_id=current_agent_id,
            call_depth=call_depth + 1,
            context=sub_context,
        )
        return res
    except Exception as exc:
        logger.error("Error executing message_agent to %s: %s", target_agent_id, exc, exc_info=True)
        return f"Error executing message_agent to target '{target_agent_id}': {exc}"


def send_email(
    email_service: EmailService | None,
    to_email: str,
    subject: str,
    body: str,
    is_html: bool = False,
    attachments: list[str] | None = None,
    conversation_id: str | None = None,
    base_dir: str | Path | None = None,
    **kwargs: Any,
) -> str:
    """
    Dispatches an email and resolves body-referenced local files.

    Args:
        email_service: Email service instance.
        to_email: Recipient email address.
        subject: Email subject.
        body: Plaintext or HTML email body.
        is_html: Flag indicating if body is HTML.
        attachments: List of file paths to attach.
        conversation_id: Optional conversation sandbox ID.
        base_dir: Target base directory to resolve attachments from.

    Returns:
        str: Dispatch confirmation message or error string.
    """
    if not email_service:
        return "Error: EmailService is not configured in the tool registry."

    resolved_attachments = list(attachments or [])
    target_base = Path(base_dir or ".").resolve()

    # 1. Resolve explicit attachments
    final_attachments: list[str] = []
    for att in resolved_attachments:
        if found := locate_file(att, target_base, conversation_id):
            final_attachments.append(str(found))
        else:
            logger.warning("Specified email attachment not found: %s", att)

    # 2. Extract referenced attachments from body
    file_refs = re.findall(
        r"([a-zA-Z0-9_\-]+\.(?:png|jpg|jpeg|webp|pdf|txt|csv))",
        body,
        re.IGNORECASE,
    )
    processed_body = body

    for raw_ref in set(file_refs):
        if found := locate_file(raw_ref, target_base, conversation_id):
            path_str = str(found)
            if path_str not in final_attachments:
                final_attachments.append(path_str)

            md_pattern = rf"!\[.*?\]\([^)]*{re.escape(found.name)}[^)]*\)"
            processed_body = re.sub(md_pattern, "", processed_body)
            html_pattern = rf'<img\s+[^>]*src=["\'][^"\']*{re.escape(found.name)}["\'][^>]*>'
            processed_body = re.sub(html_pattern, "", processed_body, flags=re.IGNORECASE)

    try:
        return email_service.send_email(
            to_email=to_email,
            subject=subject,
            body=processed_body,
            is_html=is_html,
            attachments=final_attachments,
        )
    except Exception as exc:
        logger.error("Error executing send_email: %s", exc, exc_info=True)
        return f"Error executing send_email: {exc}"
