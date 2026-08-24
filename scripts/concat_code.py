#!/usr/bin/env python3

"""
Codebase Aggregation Utility Script.

This script recursively scans the project directory, filters out specified directories
(such as virtual environments, cache folders, and version control metadata), reads all matching
Python source files, and concatenates their contents into a single formatted summary file (`codebase_summary.txt`).
"""

import os, argparse

# Target destination text file where the concatenated codebase summary will be saved
OUTPUT_FILE = "codebase_summary.txt"

# Set of directory paths or names to ignore during filesystem traversal (normalisiert)
IGNORE_DIRS = {
    os.path.normpath(p)
    for p in {
        "venv",
        ".venv",
        "instance",
        "migrations",
        "docs",
        "app/domains",
        "app/repositories",
        "app/routes",
        "app/storage",
        "__pycache__",
        ".git",
        ".pytest_cache",
        ".idea",
        ".vscode",
    }
}

# Set of specific file names to ignore during aggregation
IGNORE_FILES = {
    "concat_code.py",
    OUTPUT_FILE,
}

# Allowed file extensions to include in the output file
ALLOWED_EXTENSIONS = {".py"}


def collect_code(
    target_dir: str = ".", output_file: str = OUTPUT_FILE
) -> None:
    """Traverses `target_dir`, filters ignored directories/files, and concatenates code."""
    target_dir = os.path.abspath(target_dir)

    with open(output_file, "w", encoding="utf-8") as out:
        for current_root, dirs, files in os.walk(target_dir):
            dirs[:] = [
                d
                for d in dirs
                if d not in IGNORE_DIRS
                and os.path.normpath(
                    os.path.relpath(os.path.join(current_root, d), target_dir)
                )
                not in IGNORE_DIRS
            ]

            for file in sorted(files):
                if file in IGNORE_FILES:
                    continue

                _, ext = os.path.splitext(file)
                if ext.lower() in ALLOWED_EXTENSIONS:
                    full_path = os.path.join(current_root, file)
                    rel_path = os.path.relpath(full_path, target_dir)

                    out.write(f"# Datei: {rel_path}\n")

                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            out.write(f.read())
                    except Exception as e:
                        out.write(f"# [Error reading file: {e}]\n")

                    out.write("\n\n")

    print(
        f"Done! Codebase from '{target_dir}' was successfully written to '{output_file}'."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Concatenate codebase files into a single text file."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target directory to scan (default: current directory)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=OUTPUT_FILE,
        help="Output summary file path",
    )

    args = parser.parse_args()
    collect_code(target_dir=args.target, output_file=args.output)
