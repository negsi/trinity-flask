"""
File Storage Service Module.

Provides centralized abstractions for local filesystem operations, secure file uploads,
sandboxed disk writes, and text extraction from documents (PDFs, plain text).
"""

import logging
from pathlib import Path
import uuid
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

import pypdf

from app.config import BaseConfig
from app.domain.errors import InvalidFileError, StorageError

logger = logging.getLogger(__name__)


class FileStorageService:
    """Centralized service managing filesystem storage, sandboxing, and document text extraction."""

    def resolve_sandbox_target(
        self,
        file_path: str | Path,
        base_dir: str | Path,
        sandbox_id: str | None = None,
    ) -> tuple[Path, Path]:
        """
        Resolves the active sandbox root directory and the target path.
        Routes paths starting with 'shared' or 'shared/' to the global SHARED_FOLDER.

        Args:
            file_path: Relative or absolute target path.
            base_dir: Base root directory for conversation workspaces.
            sandbox_id: Optional conversation subfolder identifier.

        Returns:
            tuple[Path, Path]: (target_sandbox_dir, resolved_target_path)

        Raises:
            StorageError: If the resolved path escapes the active sandbox root.
        """
        raw_str = str(file_path).strip().replace("\\", "/")
        clean_rel = raw_str.lstrip("/")

        if clean_rel == "shared" or clean_rel.startswith("shared/"):
            shared_root = getattr(
                BaseConfig,
                "SHARED_FOLDER",
                Path(base_dir).resolve().parent / "shared",
            )
            target_dir = Path(shared_root).resolve()
            sub_path_str = clean_rel[len("shared"):].lstrip("/")
            raw_path = Path(sub_path_str) if sub_path_str else Path(".")
        else:
            base_root = Path(base_dir).resolve()
            target_dir = (base_root / sandbox_id).resolve() if sandbox_id else base_root
            raw_path = Path(file_path) if raw_str else Path(".")

        self.ensure_directory(target_dir)

        resolved_path = (
            (target_dir / raw_path).resolve()
            if not raw_path.is_absolute()
            else raw_path.resolve()
        )

        if not resolved_path.is_relative_to(target_dir):
            error_msg = f"Security Violation: Path '{resolved_path}' escapes sandbox '{target_dir}'."
            logger.error(error_msg)
            raise StorageError(error_msg)

        return target_dir, resolved_path

    @staticmethod
    def ensure_directory(directory_path: str | Path) -> Path:
        """
        Ensures that a specified directory exists, creating intermediate parents if needed.

        Args:
            directory_path: Target directory path.

        Returns:
            Path: The resolved absolute directory path.

        Raises:
            StorageError: If directory creation fails due to filesystem permissions.
        """
        target = Path(directory_path).resolve()
        try:
            target.mkdir(parents=True, exist_ok=True)
            return target
        except OSError as exc:
            logger.error("Failed to create directory '%s': %s", target, exc, exc_info=True)
            raise StorageError(f"Failed to create storage directory '{target}': {exc}") from exc

    def save_file(
        self,
        file: FileStorage,
        target_folder: str | Path,
    ) -> tuple[str, str, int, str]:
        """
        Persists an uploaded file to the target directory with a unique UUID filename prefix.

        Args:
            file: Werkzeug uploaded file wrapper.
            target_folder: Absolute or relative folder destination path.

        Returns:
            tuple[str, str, int, str]: Tuple of (unique_filename, full_path, file_size_bytes, mime_type).

        Raises:
            InvalidFileError: If the file object is missing or has no filename.
            StorageError: If disk write operations fail.
        """
        if not file or not file.filename:
            raise InvalidFileError("No valid file payload or filename provided.")

        folder_path = self.ensure_directory(target_folder)
        original_name = secure_filename(file.filename) or "unnamed_file"
        unique_filename = f"{uuid.uuid4()}_{original_name}"
        full_path = folder_path / unique_filename

        try:
            file.save(str(full_path))
            file_size = full_path.stat().st_size
            mime_type = file.content_type or "application/octet-stream"
            logger.info("Saved file '%s' (%d bytes) to '%s'", unique_filename, file_size, full_path)
            return unique_filename, str(full_path), file_size, mime_type
        except OSError as exc:
            logger.error("Failed to save file to '%s': %s", full_path, exc, exc_info=True)
            raise StorageError(f"Failed to write file to disk: {exc}") from exc

    def delete_file(self, file_path: str | Path | None) -> bool:
        """
        Deletes a file from disk if it exists.

        Args:
            file_path: Path of the file to remove.

        Returns:
            bool: True if the file was deleted, False if it did not exist or was None.

        Raises:
            StorageError: If deletion fails due to filesystem permissions.
        """
        if not file_path:
            return False

        target = Path(file_path).resolve()
        if not target.is_file():
            logger.warning("Attempted to delete non-existent file: %s", target)
            return False

        try:
            target.unlink()
            logger.info("Successfully deleted file: %s", target)
            return True
        except OSError as exc:
            logger.error("Error deleting file '%s': %s", target, exc, exc_info=True)
            raise StorageError(f"Failed to delete file '{target}': {exc}") from exc

    def extract_text_content(
        self,
        file_path_str: str | Path,
        mime_type: str | None = None,
    ) -> str | None:
        """
        Extracts textual content from local PDF or plain text documents.

        Args:
            file_path_str: Path to the target document.
            mime_type: Optional MIME type string for parser selection.

        Returns:
            str | None: Extracted text content or None if extraction fails or file is absent.
        """
        target = Path(file_path_str).resolve()
        if not target.is_file():
            logger.warning("File does not exist for text extraction: %s", target)
            return None

        is_pdf = (mime_type == "application/pdf") or (target.suffix.lower() == ".pdf")
        if is_pdf:
            return self._extract_pdf_text(target)

        return self._extract_plain_text(target)

    def write_sandboxed_file(
        self,
        file_path: str | Path,
        content: str | bytes | None = "",
        base_dir: str | Path = ".",
        sandbox_id: str | None = None,
        mode: str = "w",
    ) -> str:
        """
        Safely writes content to disk or creates an empty directory,
        guarding strictly against directory traversal.

        Args:
            file_path: Relative or absolute target path (supports 'shared/...' prefix).
            content: Payload to write (str, bytes, or None/empty for directory creation).
            base_dir: Base root directory for workspaces.
            sandbox_id: Optional workspace subfolder identifier.
            mode: File write mode ('w', 'a', 'wb', 'ab').

        Returns:
            str: Informational message detailing the operation result.

        Raises:
            StorageError: If security boundaries are violated or write fails.
        """
        target_dir, resolved_path = self.resolve_sandbox_target(
            file_path=file_path,
            base_dir=base_dir,
            sandbox_id=sandbox_id,
        )

        raw_str = str(file_path).strip().replace("\\", "/")
        is_empty_content = content is None or content == "" or content == b""
        is_dir_request = raw_str.endswith("/") or (is_empty_content and not resolved_path.suffix)

        # Handle pure directory creation (e.g. "shared/foobar" with empty content)
        if is_dir_request:
            try:
                resolved_path.mkdir(parents=True, exist_ok=True)
                logger.info("Created directory '%s'", resolved_path)
                return f"Successfully created directory '{resolved_path.name}' at '{resolved_path}'."
            except OSError as exc:
                logger.error("Failed creating directory '%s': %s", resolved_path, exc, exc_info=True)
                raise StorageError(f"Error creating directory '{file_path}': {exc}") from exc

        valid_modes = {"w", "a", "wb", "ab"}
        normalized_mode = f"{mode}b" if isinstance(content, bytes) and mode in {"w", "a"} else mode

        if normalized_mode not in valid_modes:
            raise StorageError(f"Invalid write mode '{mode}'. Supported: {sorted(valid_modes)}")

        try:
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            is_binary = "b" in normalized_mode
            encoding = None if is_binary else "utf-8"

            with open(resolved_path, mode=normalized_mode, encoding=encoding) as file_handle:
                file_handle.write(content)

            action = "Appended to" if "a" in normalized_mode else "Successfully wrote to"
            unit = "bytes" if is_binary else "characters"
            size = len(content)
            logger.info("%s file '%s' (%d %s)", action, resolved_path, size, unit)
            return f"{action} file '{resolved_path.name}' at '{resolved_path}' ({size} {unit} written)."
        except OSError as exc:
            logger.error("Failed writing sandboxed file '%s': %s", resolved_path, exc, exc_info=True)
            raise StorageError(f"Error writing to file '{file_path}': {exc}") from exc

    def read_sandboxed_file(
        self,
        file_path: str | Path,
        base_dir: str | Path,
        sandbox_id: str | None = None,
        encoding: str = "utf-8",
    ) -> str:
        """
        Safely reads text content from disk, guarding strictly against directory traversal.

        Args:
            file_path: Relative or absolute target path (supports 'shared/...' prefix).
            base_dir: Base root directory for workspaces.
            sandbox_id: Optional workspace subfolder identifier.
            encoding: Text character encoding (defaults to 'utf-8').

        Returns:
            str: Raw text content of the file.

        Raises:
            StorageError: If security boundaries are violated, file does not exist, or read fails.
        """
        _, resolved_path = self.resolve_sandbox_target(
            file_path=file_path,
            base_dir=base_dir,
            sandbox_id=sandbox_id,
        )

        if not resolved_path.is_file():
            raise StorageError(f"File '{file_path}' does not exist inside sandbox.")

        try:
            content = resolved_path.read_text(encoding=encoding)
            logger.info("Successfully read file '%s' (%d characters)", resolved_path, len(content))
            return content
        except OSError as exc:
            logger.error("Failed reading sandboxed file '%s': %s", resolved_path, exc, exc_info=True)
            raise StorageError(f"Error reading file '{file_path}': {exc}") from exc

    def _extract_pdf_text(self, path: Path) -> str | None:
        """Helper extracting pages from a PDF document safely."""
        try:
            reader = pypdf.PdfReader(str(path))
            pages_text = [
                f"--- Page {idx + 1} ---\n{text}"
                for idx, page in enumerate(reader.pages)
                if (text := page.extract_text())
            ]
            return "\n\n".join(pages_text).strip() if pages_text else None
        except Exception as exc:
            logger.error("Failed to extract PDF text from '%s': %s", path, exc, exc_info=True)
            return None

    def _extract_plain_text(self, path: Path) -> str | None:
        """Helper reading utf-8 plain text documents safely."""
        try:
            return path.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError as exc:
            logger.error("Failed to read text file '%s': %s", path, exc, exc_info=True)
            return None
