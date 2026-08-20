"""
Message Attachment Service Module.

Handles physical file storage and entity creation for chat message attachments.
"""

import logging
import mimetypes
from pathlib import Path
import uuid
from werkzeug.datastructures import FileStorage

from app.domain.models.message import MessageAttachment
from app.services.infrastructure.file_storage_service import FileStorageService

logger = logging.getLogger(__name__)


class MessageAttachmentService:
    """Service managing uploaded chat message attachments and sandbox storage."""

    def __init__(
        self,
        file_storage_service: FileStorageService,
        upload_folder: str | Path,
        conversations_folder: str | Path | None = None,
    ) -> None:
        self.file_storage_service = file_storage_service
        self.upload_folder = Path(upload_folder).resolve()
        self.conversations_folder = (
            Path(conversations_folder).resolve() if conversations_folder else self.upload_folder
        )
        self.file_storage_service.ensure_directory(self.upload_folder)
        self.file_storage_service.ensure_directory(self.conversations_folder)

    def save_attachment_file(
        self,
        file: FileStorage,
        conversation_id: str | None = None,
    ) -> MessageAttachment:
        """
        Saves an incoming uploaded file into the conversation sandbox directory.

        Args:
            file: Incoming uploaded file wrapper.
            conversation_id: Associated conversation identifier.

        Returns:
            MessageAttachment: Persisted metadata model for the attachment.
        """
        original_filename = file.filename or "attachment"
        attachment_id = str(uuid.uuid4())
        stored_filename = f"{attachment_id}_{original_filename}"

        target_dir = (
            self.conversations_folder / conversation_id if conversation_id else self.conversations_folder
        )
        self.file_storage_service.ensure_directory(target_dir)

        destination_path = target_dir / stored_filename
        file.save(str(destination_path))

        file_size = destination_path.stat().st_size
        guessed_mime, _ = mimetypes.guess_type(original_filename)
        resolved_mime = guessed_mime or file.content_type or "application/octet-stream"

        return MessageAttachment(
            id=attachment_id,
            name=original_filename,
            filename=stored_filename,
            file_path=str(destination_path),
            file_size=file_size,
            mime_type=resolved_mime,
        )

    def delete_attachment_file(self, file_path: str | Path | None) -> None:
        """
        Removes an attachment file from physical storage.

        Args:
            file_path: Absolute or relative path to the attachment file.
        """
        if file_path:
            self.file_storage_service.delete_file(file_path)
