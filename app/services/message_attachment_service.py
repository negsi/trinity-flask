"""
Message Attachment File Service.

Handles local storage uploads, file path generation, and entity persistence for message attachments.
"""

import logging
import os
import uuid
from typing import Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from app.domain.models.message_attachment import MessageAttachment

logger = logging.getLogger(__name__)


class MessageAttachmentService:
    """Service managing uploaded chat attachment storage."""

    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder

        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

    def save_attachment_file(
        self, file: FileStorage, message_id: Optional[str] = None
    ) -> MessageAttachment:
        """
        Saves an uploaded file to disk and constructs a MessageAttachment domain entity.

        Args:
            file (FileStorage): Werkzeug uploaded file wrapper.
            message_id (Optional[str]): Parent message ID link.

        Returns:
            MessageAttachment: Constructed attachment entity.
        """
        if not file or not file.filename:
            raise ValueError("NO_VALID_FILE_PROVIDED")

        orig_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{orig_filename}"
        full_path = os.path.join(self.upload_folder, unique_filename)
        file.save(full_path)
        file_size = os.path.getsize(full_path)

        return MessageAttachment(
            name=file.filename,
            filename=unique_filename,
            file_path=full_path,
            mime_type=file.content_type or "application/octet-stream",
            file_size=file_size,
            message_id=message_id,
        )

    def delete_attachment_file(self, file_path: str) -> None:
        """Removes physical file from disk."""
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                logger.error("Error removing file %s: %s", file_path, e, exc_info=True)
