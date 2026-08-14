"""
Datasource Application Service Module.

Handles knowledge base document uploads, file storage management, and entity persistence.
"""

import logging
from typing import Optional
from werkzeug.datastructures import FileStorage

from app.domain.errors import DatasourceNotFoundError, InvalidFileError
from app.domain.models.datasource import Datasource
from app.domain.repositories.datasource_repository import DatasourceRepository
from app.services.file_storage_service import FileStorageService

logger = logging.getLogger(__name__)


class DatasourceService:
    """Service managing uploaded agent knowledge base documents."""

    def __init__(
        self,
        datasource_repo: DatasourceRepository,
        file_storage_service: FileStorageService,
        upload_folder: str,
    ) -> None:
        self.datasource_repo = datasource_repo
        self.file_storage_service = file_storage_service
        self.upload_folder = upload_folder
        self.file_storage_service.ensure_directory(self.upload_folder)

    def process_and_save_file(
        self,
        file: FileStorage,
        display_name: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Datasource:
        """
        Saves an uploaded document to disk and persists its metadata in the repository.

        Args:
            file (FileStorage): Werkzeug uploaded file object.
            display_name (Optional[str]): User-friendly display name.
            agent_id (Optional[str]): Associated Agent ID.

        Returns:
            Datasource: The persisted datasource domain entity.

        Raises:
            InvalidFileError: If the uploaded file is invalid.
            StorageError: If disk storage fails.
        """
        if not file or not file.filename:
            raise InvalidFileError("No valid file payload provided for datasource creation.")

        unique_filename, full_path, file_size, mime_type = self.file_storage_service.save_file(
            file=file,
            target_folder=self.upload_folder,
        )

        datasource = Datasource(
            name=display_name or file.filename,
            filename=unique_filename,
            file_path=full_path,
            mime_type=mime_type,
            file_size=file_size,
            agent_id=agent_id,
        )

        saved_datasource = self.datasource_repo.save(datasource)
        logger.info("Persisted Datasource '%s' for agent '%s'", saved_datasource.id, agent_id)
        return saved_datasource

    def delete_datasource(
        self,
        datasource_id: str,
        agent_id: Optional[str] = None,
    ) -> None:
        """
        Deletes a datasource record and removes its physical file from storage.

        Args:
            datasource_id (str): Unique datasource identifier.
            agent_id (Optional[str]): Optional parent agent ID for scope validation.

        Raises:
            DatasourceNotFoundError: If the datasource record is missing.
        """
        datasource = self.datasource_repo.get_by_id(datasource_id)
        if not datasource:
            raise DatasourceNotFoundError(f"Datasource with ID '{datasource_id}' was not found.")

        if agent_id and datasource.agent_id != agent_id:
            raise DatasourceNotFoundError(
                f"Datasource '{datasource_id}' is not associated with agent '{agent_id}'."
            )

        if datasource.file_path:
            self.file_storage_service.delete_file(datasource.file_path)

        self.datasource_repo.delete(datasource_id)
        logger.info("Deleted Datasource entity '%s'", datasource_id)
