"""
Message Attachment Service Module.

Handles storage and entity lifecycle for attachments associated with chat messages.
"""

import logging
from typing import Optional
from werkzeug.datastructures import FileStorage

from app.domain.errors import InvalidFileError
from app.domain.models.message_attachment import MessageAttachment
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
        message_id: Optional[str] = None,
    ) -> MessageAttachment:
        """
        Persists an attachment file to disk and constructs a domain model.

        Args:
            file (FileStorage): Uploaded file wrapper.
            message_id (Optional[str]): Optional parent message ID.

        Returns:
            MessageAttachment: The constructed attachment domain entity.

        Raises:
            InvalidFileError: If the uploaded file is empty or missing.
        """
        if not file or not file.filename:
            raise InvalidFileError("No valid file provided for message attachment.")

        unique_filename, full_path, file_size, mime_type = self.file_storage_service.save_file(
            file=file,
            target_folder=self.upload_folder,
        )

        return MessageAttachment(
            name=file.filename,
            filename=unique_filename,
            file_path=full_path,
            mime_type=mime_type,
            file_size=file_size,
            message_id=message_id,
        )

    def delete_attachment_file(self, file_path: str) -> None:
        """
        Removes an attachment file from physical storage.

        Args:
            file_path (str): Absolute or relative path to the attachment file.
        """
        self.file_storage_service.delete_file(file_path)
