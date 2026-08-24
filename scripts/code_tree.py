#!/usr/bin/env python3

import ast
import os
from pathlib import Path

IGNORE_DIRS = {
    "venv", ".venv", "instance", "migrations", "docs",
    "__pycache__", ".git", ".pytest_cache", ".idea", ".vscode"
}

def parse_python_symbols(file_path: Path) -> list[str]:
    """Extracts top-level functions, variables, and classes with their members."""
    symbols = []
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError, PermissionError):
        return symbols

    for node in tree.body:
        # Top-Level Funktionen
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(f"  ├── fn: {node.name}()")

        # Top-Level Variablen
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbols.append(f"  ├── var: {target.id}")
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                symbols.append(f"  ├── var: {node.target.id}")

        # Klassendeklarationen + deren Member & Methoden
        elif isinstance(node, ast.ClassDef):
            symbols.append(f"  ├── class: {node.name}")
            class_members = set()

            for item in node.body:
                # Methoden
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    class_members.add(f"  │   ├── method: {item.name}()")
                    # Attribute aus __init__ (self.attribute) parsen
                    if item.name == "__init__":
                        for stmt in ast.walk(item):
                            if isinstance(stmt, ast.Attribute) and isinstance(stmt.value, ast.Name) and stmt.value.id == "self":
                                class_members.add(f"  │   ├── field: self.{stmt.attr}")

                # Klassenvariablen (z. B. class_var = 1 oder class_var: int)
                elif isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            class_members.add(f"  │   ├── field: {target.id}")
                elif isinstance(item, ast.AnnAssign):
                    if isinstance(item.target, ast.Name):
                        class_members.add(f"  │   ├── field: {item.target.id}")

            symbols.extend(sorted(class_members))

    return symbols


def print_tree_with_symbols(root_dir: str = ".") -> None:
    root_path = Path(root_dir).resolve()

    for current_root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        rel_path = Path(current_root).relative_to(root_path)
        indent_level = len(rel_path.parts) if rel_path != Path(".") else 0
        indent = "    " * indent_level

        folder_name = rel_path.name if rel_path != Path(".") else root_path.name
        print(f"{indent}📂 {folder_name}/")

        file_indent = "    " * (indent_level + 1)
        for file in sorted(files):
            file_path = Path(current_root) / file
            print(f"{file_indent}📄 {file}")

            if file.endswith(".py"):
                symbols = parse_python_symbols(file_path)
                symbol_indent = "    " * (indent_level + 2)
                for sym in symbols:
                    print(f"{symbol_indent}{sym}")


if __name__ == "__main__":
    print_tree_with_symbols(".")