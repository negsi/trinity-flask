"""
Codebase Aggregation Utility Script.

This script recursively scans the project directory, filters out specified directories
(such as virtual environments, cache folders, and version control metadata), reads all matching
Python source files, and concatenates their contents into a single formatted summary file (`codebase_summary.txt`).
"""

import os

# Target destination text file where the concatenated codebase summary will be saved
OUTPUT_FILE = "codebase_summary.txt"

# Set of directory names to ignore during filesystem traversal
IGNORE_DIRS = {
    "venv",
    ".venv",
    "instance",
    "migrations",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".idea",
    ".vscode",
}

# Set of specific file names to ignore during aggregation
IGNORE_FILES = {
    "concat_code.py",
    OUTPUT_FILE,
}

# Allowed file extensions to include in the output file
ALLOWED_EXTENSIONS = {".py"}


def collect_code(root_dir: str = ".") -> None:
    """
    Traverses the directory tree from `root_dir`, filters out ignored directories/files,
    and appends the contents of matching source files into a unified text file.

    Args:
        root_dir (str): Root directory path from which to start scanning. Defaults to "." (current directory).
    """
    # Open the summary destination file in write mode with UTF-8 encoding
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for current_root, dirs, files in os.walk(root_dir):
            # Prune directory search list in-place to skip ignored folders
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            # Process files in alphabetical order for deterministic output
            for file in sorted(files):
                # Skip explicitly ignored files
                if file in IGNORE_FILES:
                    continue

                # Check if file extension matches allowed file types
                _, ext = os.path.splitext(file)
                if ext.lower() in ALLOWED_EXTENSIONS:
                    full_path = os.path.join(current_root, file)
                    rel_path = os.path.relpath(full_path, root_dir)

                    # Write file identifier header
                    out.write(f"# Datei: {rel_path}\n")

                    # Attempt to read and append the target file content
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            out.write(f.read())
                    except Exception as e:
                        out.write(f"# [Error reading file: {e}]\n")

                    # Add blank lines as separator between files
                    out.write("\n\n")

    print(f"Done! Codebase was successfully written to '{OUTPUT_FILE}'.")


if __name__ == "__main__":
    # Execute code collection when run directly as main script
    collect_code()