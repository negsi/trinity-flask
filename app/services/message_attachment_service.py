"""
Message Attachment Service Module.

Handles storage and entity lifecycle for attachments associated with chat messages.
"""

import os, logging, uuid, mimetypes
from flask import current_app
from typing import Optional
from werkzeug.datastructures import FileStorage

from app.domain.errors import InvalidFileError
from app.domain.models.message import MessageAttachment
from app.services.file_storage_service import FileStorageService

logger = logging.getLogger(__name__)


class MessageAttachmentService:
    """Service managing uploaded chat message attachments."""

    def __init__(
        self,
        file_storage_service: FileStorageService,
        upload_folder: str,
    ) -> None:
        self.file_storage_service = file_storage_service
        self.upload_folder = upload_folder
        self.file_storage_service.ensure_directory(self.upload_folder)

    def save_attachment_file(
        self,
        file: FileStorage,
        conversation_id: str = None,
    ) -> MessageAttachment:
        """Saves an incoming upload file directly into the conversation sandbox directory."""
        original_filename = file.filename
        file_uuid = str(uuid.uuid4())

        stored_filename = f"{file_uuid}_{original_filename}"

        # Safely resolve conversations_folder from instance or flask app config
        base_dir = getattr(self, "conversations_folder", None) or current_app.config.get(
            "CONVERSATIONS_FOLDER",
            os.path.join(current_app.root_path, "..", "instance", "conversations"),
        )

        if conversation_id:
            target_dir = os.path.abspath(os.path.join(base_dir, conversation_id))
        else:
            target_dir = os.path.abspath(base_dir)

        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, stored_filename)

        file.save(file_path)

        mime_type, _ = mimetypes.guess_type(original_filename)

        return MessageAttachment(
            id=file_uuid,
            name=original_filename,
            filename=stored_filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            mime_type=mime_type or file.content_type or "application/octet-stream",
        )

    def delete_attachment_file(self, file_path: str) -> None:
        """
        Removes an attachment file from physical storage.

        Args:
            file_path (str): Absolute or relative path to the attachment file.
        """
        self.file_storage_service.delete_file(file_path)
