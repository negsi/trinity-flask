"""
File Storage Service Module.

Provides centralized abstractions for local filesystem operations, secure file uploads,
sandboxed disk writes, and text extraction from documents (PDFs, plain text).
"""

import logging
import os
from pathlib import Path
from typing import Optional, Tuple, Union
import uuid

import pypdf
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.domain.errors import InvalidFileError, StorageError

logger = logging.getLogger(__name__)


class FileStorageService:
    """Centralized service managing filesystem storage, sandboxing, and document text extraction."""

    @staticmethod
    def ensure_directory(directory_path: str) -> None:
        """
        Ensures that a specified directory exists, creating it if necessary.

        Args:
            directory_path (str): Target directory path.

        Raises:
            StorageError: If directory creation fails.
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
        except OSError as e:
            logger.error("Failed to create directory '%s': %s", directory_path, e, exc_info=True)
            raise StorageError(f"Failed to create storage directory '{directory_path}': {e}") from e

    def save_file(
        self,
        file: FileStorage,
        target_folder: str,
    ) -> Tuple[str, str, int, str]:
        """
        Persists an uploaded file to the target directory with a unique filename prefix.

        Args:
            file (FileStorage): Werkzeug uploaded file wrapper.
            target_folder (str): Absolute or relative folder destination path.

        Returns:
            Tuple[str, str, int, str]: A tuple of (unique_filename, full_path, file_size_bytes, mime_type).

        Raises:
            InvalidFileError: If the file object is missing or has no filename.
            StorageError: If disk write operations fail.
        """
        if not file or not file.filename:
            raise InvalidFileError("No valid file payload or filename provided.")

        self.ensure_directory(target_folder)

        orig_filename = secure_filename(file.filename)
        if not orig_filename:
            orig_filename = "unnamed_file"

        unique_filename = f"{uuid.uuid4()}_{orig_filename}"
        full_path = os.path.abspath(os.path.join(target_folder, unique_filename))

        try:
            file.save(full_path)
            file_size = os.path.getsize(full_path)
            mime_type = file.content_type or "application/octet-stream"
            logger.info("Saved file '%s' (%d bytes) to '%s'", unique_filename, file_size, full_path)
            return unique_filename, full_path, file_size, mime_type
        except OSError as e:
            logger.error("Failed to save file to '%s': %s", full_path, e, exc_info=True)
            raise StorageError(f"Failed to write file to disk: {e}") from e

    def delete_file(self, file_path: str) -> bool:
        """
        Deletes a file from disk if it exists.

        Args:
            file_path (str): Path of the file to remove.

        Returns:
            bool: True if the file was deleted, False if it did not exist.

        Raises:
            StorageError: If deletion fails due to filesystem permissions.
        """
        if not file_path:
            return False

        path = Path(file_path)
        if not path.exists():
            logger.warning("Attempted to delete non-existent file: %s", file_path)
            return False

        try:
            path.unlink()
            logger.info("Successfully deleted file: %s", file_path)
            return True
        except OSError as e:
            logger.error("Error deleting file '%s': %s", file_path, e, exc_info=True)
            raise StorageError(f"Failed to delete file '{file_path}': {e}") from e

    def extract_text_content(
        self,
        file_path_str: str,
        mime_type: Optional[str] = None,
    ) -> Optional[str]:
        """
        Extracts textual content from local PDF or plain text documents.

        Args:
            file_path_str (str): Path to the target document.
            mime_type (Optional[str]): Optional MIME type string for parser selection.

        Returns:
            Optional[str]: Extracted text content or None if extraction fails.
        """
        path = Path(file_path_str)
        if not path.exists():
            logger.warning("File does not exist for text extraction: %s", file_path_str)
            return None

        is_pdf = (mime_type == "application/pdf") or (path.suffix.lower() == ".pdf")

        if is_pdf:
            try:
                reader = pypdf.PdfReader(str(path))
                extracted_pages = []
                for idx, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        extracted_pages.append(f"--- Page {idx + 1} ---\n{page_text}")
                return "\n\n".join(extracted_pages).strip()
            except Exception as e:
                logger.error("Failed to extract PDF text from '%s': %s", file_path_str, e, exc_info=True)
                return None

        try:
            return path.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception as e:
            logger.error("Failed to read text file '%s': %s", file_path_str, e, exc_info=True)
            return None

    def write_sandboxed_file(
        self,
        file_path: str,
        content: Union[str, bytes],
        base_dir: str,
        sandbox_id: Optional[str] = None,
        mode: str = "w",
    ) -> str:
        """
        Safely writes content (str or bytes) to disk, guarding against directory traversal attacks.

        Args:
            file_path (str): Relative or absolute target path.
            content (Union[str, bytes]): Payload to write (string or raw bytes).
            base_dir (str): Base root directory for workspaces.
            sandbox_id (Optional[str]): Workspace subfolder identifier (e.g. conversation_id).
            mode (str): File write mode ('w', 'a', 'wb', 'ab').

        Returns:
            str: Status message detailing the operation result.

        Raises:
            StorageError: If security boundaries are violated or write fails.
        """
        if isinstance(content, bytes) and mode in ("w", "a"):
            mode = f"{mode}b"

        valid_modes = ("w", "a", "wb", "ab")
        if mode not in valid_modes:
            raise StorageError(f"Invalid write mode '{mode}'. Supported modes: {valid_modes}")

        target_dir = Path(base_dir).resolve()
        if sandbox_id:
            target_dir = (target_dir / sandbox_id).resolve()

        self.ensure_directory(str(target_dir))

        raw_path = Path(file_path)
        resolved_path = (target_dir / raw_path).resolve() if not raw_path.is_absolute() else raw_path.resolve()

        if not resolved_path.is_relative_to(target_dir):
            error_msg = f"Security Violation: Target path '{resolved_path}' is outside sandbox '{target_dir}'."
            logger.error(error_msg)
            raise StorageError(error_msg)

        try:
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            
            is_binary = "b" in mode
            open_kwargs = {"mode": mode}
            if not is_binary:
                open_kwargs["encoding"] = "utf-8"

            with open(resolved_path, **open_kwargs) as f:
                f.write(content)

            action = "Appended to" if "a" in mode else "Successfully wrote to"
            unit = "bytes" if is_binary else "characters"
            size = len(content)
            logger.info("%s file '%s' (%d %s)", action, resolved_path, size, unit)
            return f"{action} file '{resolved_path.name}' at '{resolved_path}' ({size} {unit} written)."
        except OSError as e:
            logger.error("Failed writing to sandboxed file '%s': %s", resolved_path, e, exc_info=True)
            raise StorageError(f"Error writing to file '{file_path}': {e}") from e
