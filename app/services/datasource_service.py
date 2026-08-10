"""
Datasource File Service.

Handles local storage uploads, file path generation, and entity persistence for agent knowledge sources.
"""

import logging
import os
import uuid
from typing import Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from app.domain.models.datasource import Datasource
from app.domain.repositories.datasource_repository import DatasourceRepository

logger = logging.getLogger(__name__)


class DatasourceService:
    """Service managing uploaded document storage and database records."""

    def __init__(self, datasource_repo: DatasourceRepository, upload_folder: str):
        self.datasource_repo = datasource_repo
        self.upload_folder = upload_folder

        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

    def process_and_save_file(
        self,
        file: FileStorage,
        display_name: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Datasource:
        """
        Saves an uploaded file to disk and persists its metadata in the database repository.

        Args:
            file (FileStorage): Werkzeug uploaded file wrapper.
            display_name (Optional[str]): UI display name.
            agent_id (Optional[str]): Parent agent ID link.

        Returns:
            Datasource: Created datasource entity.
        """
        if not file or not file.filename:
            raise ValueError("NO_VALID_FILE_PROVIDED")

        orig_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{orig_filename}"
        full_path = os.path.join(self.upload_folder, unique_filename)
        file.save(full_path)
        file_size = os.path.getsize(full_path)

        datasource = Datasource(
            name=display_name or orig_filename,
            filename=unique_filename,
            file_path=full_path,
            mime_type=file.content_type or "application/octet-stream",
            file_size=file_size,
            agent_id=agent_id,
        )

        return self.datasource_repo.save(datasource)

    def delete_datasource(
        self, datasource_id: str, agent_id: Optional[str] = None
    ) -> None:
        """Deletes a datasource record and removes its physical file from disk."""
        datasource = self.datasource_repo.get_by_id(datasource_id)
        if not datasource:
            raise ValueError(f"DATASOURCE_NOT_FOUND: '{datasource_id}'")

        if datasource.file_path and os.path.exists(datasource.file_path):
            try:
                os.remove(datasource.file_path)
            except OSError as e:
                logger.error(
                    "Error removing file %s: %s", datasource.file_path, e, exc_info=True
                )

        self.datasource_repo.delete(datasource_id)
