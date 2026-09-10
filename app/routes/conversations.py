"""Agent Conversations Endpoints."""

import mimetypes
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
from flask import Blueprint, Response, current_app, jsonify, request
from dependency_injector.wiring import inject, Provide

from app.containers import Container
from app.services.agent import AgentService
from app.services.messaging import MessagingService
from app.services.infrastructure.file_storage_service import FileStorageService

bp = Blueprint("conversations", __name__, url_prefix="/api/v1/agents/<agent_id>/conversations")


def _resolve_and_validate_path(
    conversation_id: str,
    relative_path_str: str = "",
    allow_root: bool = False,
) -> Union[Tuple[Path, Path], Tuple[Response, int]]:
    """Resolves a target path against the conversation base directory and validates sandbox constraints."""
    conversations_folder = current_app.config.get("CONVERSATIONS_FOLDER")
    if not conversations_folder:
        return jsonify({"error": "CONVERSATIONS_FOLDER is not configured."}), 500

    conv_dir = Path(conversations_folder).resolve() / conversation_id
    target_path = (conv_dir / relative_path_str.strip("/")).resolve() if relative_path_str else conv_dir

    if not target_path.is_relative_to(conv_dir):
        return jsonify({"error": "Security Violation: Target path escapes conversation sandbox."}), 400

    if not allow_root and target_path == conv_dir:
        return jsonify({"error": "Security Violation: Cannot operate directly on conversation root."}), 400

    return conv_dir, target_path


def _extract_target_path() -> Optional[str]:
    """Extracts path string parameter from JSON request body."""
    payload = request.get_json(silent=True) or {}
    path_str = payload.get("path") or payload.get("folder_path") or payload.get("file_path")
    if path_str and isinstance(path_str, str):
        return path_str
    return None


def _serialize_fs_item(item_path: Path, conv_dir: Path, conversation_id: str) -> Dict[str, Any]:
    """Serializes a filesystem item into a standard JSON metadata dictionary."""
    relative_path = item_path.relative_to(conv_dir).as_posix()
    stat = item_path.stat()
    is_dir = item_path.is_dir()

    if is_dir:
        mime_type = "inode/directory"
        file_size = 0
    else:
        mime_type_guessed, _ = mimetypes.guess_type(item_path.name)
        mime_type = mime_type_guessed or "application/octet-stream"
        file_size = stat.st_size

    return {
        "id": f"{conversation_id}_{relative_path}",
        "name": item_path.name,
        "filename": item_path.name,
        "file_path": relative_path,
        "file_size": file_size,
        "mime_type": mime_type,
        "is_dir": is_dir,
        "created_at": stat.st_ctime,
    }


@bp.route("", methods=["GET"])
@inject
def get_agent_conversations(
    agent_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
    messaging_service: MessagingService = Provide[Container.messaging_service],
):
    """Retrieves all conversations associated with a specific agent."""
    agent_service.get_agent(agent_id)
    conversations = messaging_service.get_conversations_by_agent(agent_id)
    return jsonify([conv.to_dict() for conv in conversations]), 200


@bp.route("/<conversation_id>/history", methods=["GET"])
@inject
def get_conversation_history(
    agent_id: str,
    conversation_id: str,
    limit: int = 50,
    agent_service: AgentService = Provide[Container.agent_service],
    messaging_service: MessagingService = Provide[Container.messaging_service],
):
    """Retrieves message history for a specific conversation."""
    agent_service.get_agent(agent_id)
    messages = messaging_service.get_conversation_history(
        conversation_id=conversation_id, limit=limit
    )
    return jsonify([msg.to_dict() for msg in messages]), 200


@bp.route("/<conversation_id>", methods=["DELETE"])
@inject
def delete_conversation(
    agent_id: str,
    conversation_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
    messaging_service: MessagingService = Provide[Container.messaging_service],
):
    """Deletes a specific conversation for an agent."""
    agent_service.get_agent(agent_id)
    messaging_service.delete_conversation(conversation_id)
    return "", 204


@bp.route("/<conversation_id>/files", methods=["GET"])
@inject
def get_conversation_files(
    agent_id: str,
    conversation_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
):
    """Recursively retrieves all files and directories stored inside a conversation's workspace."""
    agent_service.get_agent(agent_id)

    res = _resolve_and_validate_path(conversation_id, allow_root=True)
    if not isinstance(res, tuple) or not isinstance(res[0], Path):
        return jsonify([]), 200

    conv_dir, _ = res
    if not conv_dir.exists() or not conv_dir.is_dir():
        return jsonify([]), 200

    items_list = [
        _serialize_fs_item(item_path, conv_dir, conversation_id)
        for item_path in conv_dir.rglob("*")
    ]

    return jsonify(items_list), 200


@bp.route("/<conversation_id>/folders", methods=["POST"])
@inject
def create_conversation_folder(
    agent_id: str,
    conversation_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
):
    """Creates a new directory inside the conversation workspace."""
    agent_service.get_agent(agent_id)

    folder_path_str = _extract_target_path()
    if not folder_path_str:
        return jsonify({"error": "Field 'path' or 'folder_path' is required."}), 400

    res = _resolve_and_validate_path(conversation_id, folder_path_str, allow_root=False)
    if not isinstance(res, tuple) or not isinstance(res[0], Path):
        return res

    conv_dir, target_dir = res

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        return jsonify(_serialize_fs_item(target_dir, conv_dir, conversation_id)), 201
    except OSError as exc:
        return jsonify({"error": f"Failed to create directory: {exc}"}), 500


@bp.route("/<conversation_id>/folders", methods=["DELETE"])
@inject
def delete_conversation_folder(
    agent_id: str,
    conversation_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
):
    """Deletes a directory and all its contents recursively from the conversation workspace."""
    agent_service.get_agent(agent_id)

    folder_path_str = _extract_target_path()
    if not folder_path_str:
        return jsonify({"error": "Field 'path' or 'folder_path' is required."}), 400

    res = _resolve_and_validate_path(conversation_id, folder_path_str, allow_root=False)
    if not isinstance(res, tuple) or not isinstance(res[0], Path):
        return res

    _, target_dir = res

    if not target_dir.exists() or not target_dir.is_dir():
        return jsonify({"error": "Directory not found."}), 404

    try:
        shutil.rmtree(target_dir)
        return "", 204
    except OSError as exc:
        return jsonify({"error": f"Failed to delete directory: {exc}"}), 500


@bp.route("/<conversation_id>/files", methods=["DELETE"])
@inject
def delete_conversation_file(
    agent_id: str,
    conversation_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
):
    """Deletes a specific file from the conversation workspace."""
    agent_service.get_agent(agent_id)

    file_path_str = _extract_target_path()
    if not file_path_str:
        return jsonify({"error": "Field 'path' or 'file_path' is required."}), 400

    res = _resolve_and_validate_path(conversation_id, file_path_str, allow_root=False)
    if not isinstance(res, tuple) or not isinstance(res[0], Path):
        return res

    _, target_file = res

    if not target_file.exists() or not target_file.is_file():
        return jsonify({"error": "File not found."}), 404

    try:
        target_file.unlink()
        return "", 204
    except OSError as exc:
        return jsonify({"error": f"Failed to delete file: {exc}"}), 500


@bp.route("/<conversation_id>/files/upload", methods=["POST"])
@inject
def upload_conversation_files(
    agent_id: str,
    conversation_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
    file_storage_service: FileStorageService = Provide[Container.file_storage_service],
):
    """Uploads multiple files into a conversation workspace directory."""
    agent_service.get_agent(agent_id)

    uploaded_files = request.files.getlist("files") or request.files.getlist("files[]")
    if not uploaded_files:
        return jsonify({"error": "No files provided in request."}), 400

    target_rel_folder = request.form.get("folder_path", "").strip("/")

    res = _resolve_and_validate_path(conversation_id, target_rel_folder, allow_root=True)
    if not isinstance(res, tuple) or not isinstance(res[0], Path):
        return res

    conv_dir, target_dir = res
    file_storage_service.ensure_directory(target_dir)

    uploaded_results = []
    for file_obj in uploaded_files:
        if not file_obj or not file_obj.filename:
            continue

        file_content = file_obj.read()
        target_file_path = target_dir / file_obj.filename

        try:
            file_storage_service.write_sandboxed_file(
                file_path=target_file_path,
                content=file_content,
                base_dir=conv_dir,
                mode="wb",
            )
            uploaded_results.append(file_obj.filename)
        except Exception as exc:
            return jsonify({"error": f"Failed to upload '{file_obj.filename}': {exc}"}), 500

    return jsonify({"uploaded": uploaded_results}), 201


@bp.route("/<conversation_id>/messages/<message_id>", methods=["DELETE"])
@inject
def delete_conversation_message(
    agent_id: str,
    conversation_id: str,
    message_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
    messaging_service: MessagingService = Provide[Container.messaging_service],
):
    """Deletes a specific message from a conversation."""
    agent_service.get_agent(agent_id)
    try:
        messaging_service.delete_message(message_id)
        return "", 204
    except Exception as exc:
        return jsonify({"error": f"Failed to delete message: {exc}"}), 404


@bp.route("/<conversation_id>/messages", methods=["DELETE"])
@inject
def clear_conversation_messages(
    agent_id: str,
    conversation_id: str,
    agent_service: AgentService = Provide[Container.agent_service],
    messaging_service: MessagingService = Provide[Container.messaging_service],
):
    """Deletes all messages from a conversation (resets the chat history)."""
    agent_service.get_agent(agent_id)
    try:
        messaging_service.clear_conversation_messages(conversation_id)
        return "", 204
    except Exception as exc:
        return jsonify({"error": f"Failed to clear conversation messages: {exc}"}), 404