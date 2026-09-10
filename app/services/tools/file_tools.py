"""
File Tools Module.

Provides sandboxed file operations and path resolution helpers.
"""

import logging
from pathlib import Path
from typing import Any

from app.services.infrastructure.file_storage_service import FileStorageService

logger = logging.getLogger(__name__)


def locate_file(filename: str, target_base: Path, conversation_id: str | None = None) -> Path | None:
    """
    Helper to locate a named file across conversation sandboxes.

    Args:
        filename: Name or relative path of the file to find.
        target_base: Base directory Path to search within.
        conversation_id: Optional conversation sandbox identifier.

    Returns:
        Path | None: Resolved absolute Path if found, otherwise None.
    """
    clean_name = Path(filename).name
    candidates = [
        target_base / clean_name,
        Path(filename),
    ]
    if conversation_id:
        candidates.insert(0, target_base / conversation_id / clean_name)

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    if target_base.is_dir():
        for found_file in target_base.rglob(clean_name):
            if found_file.is_file():
                return found_file.resolve()

    return None


def get_latest_image_in_dir(directory: Path) -> Path | None:
    """
    Finds the most recently modified image file in a directory tree.

    Args:
        directory: Directory Path to scan.

    Returns:
        Path | None: Path to the most recent image, or None if none found.
    """
    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
    image_files = [f for f in directory.rglob("*") if f.is_file() and f.suffix.lower() in valid_exts]
    if not image_files:
        return None
    return max(image_files, key=lambda f: f.stat().st_mtime)


def write_file(
    file_storage_service: FileStorageService,
    file_path: str,
    content: str,
    mode: str = "w",
    conversation_id: str | None = None,
    base_dir: str | Path | None = None,
    **kwargs: Any,
) -> str:
    """
    Writes content to a sandboxed file.

    Args:
        file_storage_service: Storage service instance.
        file_path: Destination path of the file.
        content: String content to write.
        mode: File write mode ('w' or 'a').
        conversation_id: Optional conversation sandbox ID.
        base_dir: Target base directory.

    Returns:
        str: Absolute path of the written file or an error message.
    """
    target_base = str(base_dir) if base_dir else "."
    try:
        return file_storage_service.write_sandboxed_file(
            file_path=file_path,
            content=content,
            base_dir=target_base,
            sandbox_id=conversation_id,
            mode=mode,
        )
    except Exception as exc:
        logger.error("Error executing write_file tool: %s", exc, exc_info=True)
        return f"Error executing write_file: {exc}"


def read_file(
    file_storage_service: FileStorageService,
    file_path: str = ".",
    conversation_id: str | None = None,
    base_dir: str | Path | None = None,
    encoding: str = "utf-8",
    recursive: bool = False,
    **kwargs: Any,
) -> str:
    """
    Reads textual content from a sandboxed file, or lists directory contents
    if target path is a directory (flat or recursive).

    Args:
        file_storage_service: Storage service instance.
        file_path: Relative or absolute path of the file or directory to read/list.
        conversation_id: Optional conversation sandbox ID.
        base_dir: Target base directory.
        encoding: File character encoding for plain text files (defaults to 'utf-8').
        recursive: If True and file_path is a directory, recursively lists all contents.

    Returns:
        str: Raw text content, extracted document text, directory listing, or an error message.
    """
    target_base = Path(base_dir or ".").resolve()
    
    # Target directory resolution logic inside sandbox
    sandbox_dir = target_base / conversation_id if conversation_id else target_base
    target_path = (sandbox_dir / file_path).resolve() if file_path and file_path != "." else sandbox_dir

    # Security check: Ensure target path remains within sandbox
    if sandbox_dir not in target_path.parents and target_path != sandbox_dir:
        return f"Error: Access denied. Path '{file_path}' is outside the conversation sandbox."

    # --- 1. DIRECTORY LISTING FEATURE ---
    if target_path.exists() and target_path.is_dir():
        try:
            entries = []
            rel_base = target_path

            if recursive:
                paths = sorted(target_path.rglob("*"))
            else:
                paths = sorted(target_path.iterdir())

            for p in paths:
                try:
                    rel_p = p.relative_to(rel_base)
                except ValueError:
                    rel_p = p.name

                prefix = "[DIR] " if p.is_dir() else "[FILE]"
                entries.append(f"{prefix} {rel_p}")

            if not entries:
                return f"=== DIRECTORY LISTING ({target_path.name or '.'}) ===\n(Directory is empty)"

            mode_str = "RECURSIVE" if recursive else "FLAT"
            listing = "\n".join(entries)
            return f"=== DIRECTORY LISTING [{mode_str}] ({file_path or '.'}) ===\n\n{listing}"

        except Exception as exc:
            logger.error("Error listing directory '%s': %s", file_path, exc, exc_info=True)
            return f"Error listing directory '{file_path}': {exc}"

    # --- 2. FILE READING FEATURE (Existing functionality) ---
    path_obj = Path(file_path)
    ext = path_obj.suffix.lower()

    # Handle ODF documents (.odt, .ods, .odp) via manage_odf
    if ext in {".odt", ".ods", ".odp"}:
        from app.services.tools.office_tools import manage_odf

        doc_type = ext.lstrip(".")
        result = manage_odf(
            file_storage_service=file_storage_service,
            action="read",
            doc_type=doc_type,
            filename=path_obj.name,
            conversation_id=conversation_id,
            base_dir=target_base,
            **kwargs,
        )
        return str(result)

    try:
        # Resolve target path inside sandbox for PDFs and plain text
        resolved_path = locate_file(file_path, target_base, conversation_id)
        if not resolved_path or not resolved_path.is_file():
            # Fallback to direct resolution via read_sandboxed_file
            resolved_path = (
                (target_base / conversation_id / file_path).resolve()
                if conversation_id
                else (target_base / file_path).resolve()
            )

        # Handle PDF documents via extract_text_content
        if ext == ".pdf":
            extracted = file_storage_service.extract_text_content(
                file_path_str=resolved_path, mime_type="application/pdf"
            )
            if extracted:
                return f"=== PDF DOCUMENT CONTENT ({path_obj.name}) ===\n\n{extracted}"
            return f"Error: Could not extract text from PDF file '{file_path}' (file may be empty or image-only)."

        # Handle standard text files
        return file_storage_service.read_sandboxed_file(
            file_path=file_path,
            base_dir=str(target_base),
            sandbox_id=conversation_id,
            encoding=encoding,
        )

    except Exception as exc:
        logger.error("Error executing read_file tool for '%s': %s", file_path, exc, exc_info=True)
        return f"Error executing read_file: {exc}"