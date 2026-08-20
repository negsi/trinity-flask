"""
Datasource Application Service Module.

Handles knowledge base document uploads, file storage management, and entity persistence.
"""

import logging
from pathlib import Path
from werkzeug.datastructures import FileStorage

from app.domain.errors import DatasourceNotFoundError, InvalidFileError
from app.domain.models.datasource import Datasource
from app.domain.repositories.datasource_repository import DatasourceRepository
from app.services.infrastructure.file_storage_service import FileStorageService

logger = logging.getLogger(__name__)


class DatasourceService:
    """Service managing uploaded agent knowledge base documents."""

    def __init__(
        self,
        datasource_repo: DatasourceRepository,
        file_storage_service: FileStorageService,
        upload_folder: str | Path,
    ) -> None:
        self.datasource_repo = datasource_repo
        self.file_storage_service = file_storage_service
        self.upload_folder = Path(upload_folder).resolve()
        self.file_storage_service.ensure_directory(self.upload_folder)

    def process_and_save_file(
        self,
        file: FileStorage,
        display_name: str | None = None,
        agent_id: str | None = None,
    ) -> Datasource:
        """
        Saves an uploaded document to disk and persists its metadata.

        Args:
            file: Werkzeug uploaded file object.
            display_name: User-friendly display name.
            agent_id: Associated Agent ID.

        Returns:
            Datasource: The persisted datasource domain entity.

        Raises:
            InvalidFileError: If the uploaded file is missing or invalid.
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

        saved = self.datasource_repo.save(datasource)
        logger.info("Persisted Datasource '%s' for agent '%s'", saved.id, agent_id)
        return saved

    def delete_datasource(
        self,
        datasource_id: str,
        agent_id: str | None = None,
    ) -> None:
        """
        Deletes a datasource record and its underlying physical storage file.

        Args:
            datasource_id: Unique datasource identifier.
            agent_id: Optional parent agent ID for authorization/scope checks.

        Raises:
            DatasourceNotFoundError: If the datasource record does not exist.
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
