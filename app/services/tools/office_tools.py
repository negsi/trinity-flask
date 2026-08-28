"""
Office Tools Module.

Provides creation, reading, appending, and manipulation tools for OpenDocument Format (ODF) 
files (.odt, .ods, .odp) using the `odfdo` library.
"""

import io
import json
import logging
import re
from pathlib import Path
from typing import Any, Final, Literal

from odfdo import Cell, Document, DrawPage, Element, Frame, Header, Paragraph, Row, Table

from app.services.infrastructure.file_storage_service import FileStorageService
from app.services.tools.file_tools import locate_file

logger = logging.getLogger(__name__)

DocType = Literal["odt", "ods", "odp"]
ActionType = Literal["create", "read", "append", "update"]

SUPPORTED_DOC_TYPES: Final[set[str]] = {"odt", "ods", "odp"}
WRAPPER_CONTAINER_KEYS: Final[tuple[str, ...]] = (
    "content",
    "data",
    "table",
    "matrix",
    "spreadsheet",
    "sheet",
    "rows",
    "items",
)


# ==========================================
# SERIALIZATION & NORMALIZATION HELPERS
# ==========================================

def _document_to_bytes(doc: Document) -> bytes:
    """Serializes an odfdo Document instance into binary bytes."""
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _create_typed_cell(val: Any) -> Cell:
    """Creates an odfdo Cell with the correct data type (Formula, Float, or String)."""
    if val is None:
        return Cell("")

    if isinstance(val, str):
        val_str = val.strip()

        # Handle formulas (starting with '=')
        if val_str.startswith("="):
            formula_body = val_str[1:]
            # Map standard English formula names if needed or use ODF 'of:=' prefix
            return Cell(formula=f"of:={formula_body}")

        # Try to parse string numbers into floats/ints
        try:
            if "." in val_str or "," in val_str:
                num = float(val_str.replace(",", "."))
                return Cell(num, value_type="float")
            num = int(val_str)
            return Cell(num, value_type="float")
        except ValueError:
            pass

        return Cell(val_str, value_type="string")

    if isinstance(val, (int, float)):
        return Cell(val, value_type="float")

    return Cell(str(val), value_type="string")


def _normalize_content_to_matrix(content: Any) -> list[list[Any]]:
    """
    Converts diverse JSON/dict payload formats or CSV strings into a clean 2D matrix.
    Defensively unwraps nested LLM payload wrappers without forcing all values to string.
    """
    if isinstance(content, list) and len(content) == 1 and isinstance(content[0], str):
        content = content[0]

    if isinstance(content, str):
        content_str = content.strip()
        if content_str.startswith(("{", "[")):
            try:
                content = json.loads(content_str)
            except Exception:
                pass

        if isinstance(content, str) and any(sep in content_str for sep in ("\n", ";", ",")):
            delimiter = ";" if ";" in content_str else ","
            lines = [line for line in content_str.splitlines() if line.strip()]
            return [[cell.strip() for cell in line.split(delimiter)] for line in lines]

    while isinstance(content, dict):
        unwrapped_key = next((k for k in WRAPPER_CONTAINER_KEYS if k in content), None)
        if unwrapped_key is None:
            break
        content = content[unwrapped_key]

    matrix: list[list[Any]] = []

    match content:
        case list() if content and isinstance(content[0], list):
            matrix = content
        case list() if content and isinstance(content[0], dict):
            matrix = [list(row.values()) for row in content if isinstance(row, dict)]
        case dict():
            headers = content.get("headers") or content.get("columns") or []
            rows = content.get("rows") or content.get("data") or []
            if headers:
                matrix.append(list(headers))
            for r in rows:
                if isinstance(r, list):
                    matrix.append(r)
                elif isinstance(r, dict):
                    matrix.append(list(r.values()))
        case list():
            matrix = [content]
        case _:
            if content is not None:
                matrix = [[content]]

    return [row for row in matrix if isinstance(row, (list, tuple))]


def _extract_effective_content(content: Any, kwargs: dict[str, Any]) -> Any:
    """Extracts content payload falling back to alternative LLM tool arguments."""
    if content not in (None, [], "", {}):
        return content

    for key in ("content_blocks", "data", "rows", "payload"):
        if key in kwargs and kwargs[key] not in (None, [], "", {}):
            return kwargs[key]

    return []


# ==========================================
# ODT (TEXT) HELPERS
# ==========================================

def append_odt_content(body: Any, content_blocks: Any) -> None:
    """Appends new text content blocks to an existing ODT document body."""
    if isinstance(content_blocks, str):
        body.append(Paragraph(content_blocks))
        return

    blocks = [content_blocks] if isinstance(content_blocks, dict) else (content_blocks or [])

    for block in blocks:
        match block:
            case str():
                body.append(Paragraph(block))
            case dict():
                b_type = block.get("type", "paragraph")
                text = str(block.get("text", ""))
                level = int(block.get("level", 2))

                match b_type:
                    case "heading":
                        body.append(Header(level, text))
                    case "list":
                        for item in block.get("items", []):
                            body.append(Paragraph(f"• {item}"))
                    case _:
                        body.append(Paragraph(text))


def create_odt_document(title: str, content_blocks: Any) -> bytes:
    """Creates an ODT text document and returns its raw binary content."""
    doc = Document("text")
    if title:
        doc.body.append(Header(1, title))

    append_odt_content(doc.body, content_blocks)
    return _document_to_bytes(doc)


def read_odt_document(doc: Document) -> str:
    """Extracts text content and headings from an ODT file."""
    lines: list[str] = []

    for element in doc.body.children:
        tag = getattr(element, "tag", "").lower()
        text = getattr(element, "text_content", "").strip()

        if not text:
            continue

        if "header" in tag or isinstance(element, Header):
            lines.append(f"\n# {text}\n")
        else:
            lines.append(text)

    return "\n".join(lines).strip() or doc.get_formatted_text().strip()


# ==========================================
# ODS (SPREADSHEET) HELPERS
# ==========================================

def create_ods_spreadsheet(title: str, content: Any) -> bytes:
    """Creates an ODS spreadsheet document from 2D data or structured objects with typed cells."""
    doc = Document("spreadsheet")
    doc.body.clear()

    sheet_matrix = _normalize_content_to_matrix(content) or [["Keine Daten übergeben"]]
    table = Table(title or "Sheet1")

    for row_data in sheet_matrix:
        row = Row()
        for val in row_data:
            row.append_cell(_create_typed_cell(val))
        table.append_row(row)

    doc.body.append(table)
    return _document_to_bytes(doc)


def append_ods_spreadsheet(doc: Document, content: Any) -> bytes:
    """Appends new rows to the first sheet of an existing ODS spreadsheet."""
    tables = doc.body.get_tables()
    if not tables:
        return create_ods_spreadsheet("Sheet1", content)

    table = tables[0]
    sheet_matrix = _normalize_content_to_matrix(content)

    for row_data in sheet_matrix:
        row = Row()
        for val in row_data:
            row.append_cell(_create_typed_cell(val))
        table.append_row(row)

    return _document_to_bytes(doc)


def read_ods_spreadsheet(doc: Document) -> str:
    """Extracts table rows and sheet names from an ODS spreadsheet."""
    output_sheets: list[str] = []

    for table in doc.body.get_tables():
        sheet_name = getattr(table, "name", "Sheet")
        rows_text: list[str] = []

        for row in table.get_rows():
            cells = [
                str(cell.value if cell.value is not None else cell.text_content).strip()
                for cell in row.get_cells()
            ]
            if any(cells):
                rows_text.append(" | ".join(cells))

        if rows_text:
            output_sheets.append(f"=== Sheet: {sheet_name} ===\n" + "\n".join(rows_text))

    return "\n\n".join(output_sheets).strip() or doc.get_formatted_text().strip()


# ==========================================
# ODP (PRESENTATION) HELPERS
# ==========================================

def _create_slide_title_frame(title: str) -> Frame:
    """Constructs a native ODF presentation title frame."""
    frame = Frame(
        size=("23cm", "2.5cm"),
        position=("1.5cm", "1.2cm"),
        style="standard",
        text="",
    )
    frame.set_attribute("presentation:style-name", "title")
    frame.set_attribute("draw:layer", "layout")

    title_box = Element.from_tag("draw:text-box")
    title_box.append(Header(1, title))
    frame.append(title_box)
    return frame


def _create_slide_outline_frame(bullet_points: list[str]) -> Frame:
    """Constructs a native ODF presentation outline / bullet list frame."""
    frame = Frame(
        size=("23cm", "12cm"),
        position=("1.5cm", "4.0cm"),
        style="standard",
        text="",
    )
    frame.set_attribute("presentation:style-name", "outline")
    frame.set_attribute("draw:layer", "layout")

    content_box = Element.from_tag("draw:text-box")
    for pt in bullet_points:
        clean_pt = re.sub(r"^[-*•]\s*", "", pt).strip()
        if clean_pt:
            content_box.append(Paragraph(f"• {clean_pt}"))

    frame.append(content_box)
    return frame


def _parse_slide_text(slide_text: str, default_title: str) -> tuple[str, list[str]]:
    """Extracts the slide title and bullet points from a raw slide description."""
    lines = [line.strip() for line in slide_text.splitlines() if line.strip()]
    slide_title = ""
    bullet_points: list[str] = []

    for line in lines:
        cleaned = re.sub(r"(?i)^(Folie|Slide)\s*\d+:?\s*", "", line).strip()
        if not cleaned:
            continue

        if not slide_title:
            slide_title = cleaned[6:].strip() if cleaned.lower().startswith("titel:") else cleaned
            continue

        if cleaned.lower().startswith("titel:"):
            continue

        bullet_points.append(cleaned)

    return slide_title or default_title, bullet_points


def append_odp_slides(doc: Document, title: str, content_blocks: Any) -> None:
    """Appends clean presentation slides using native ODF frame elements.
    Supports raw text (split by '--' or 'Slide X'), JSON strings, and list/dict structures.
    """
    slides_data: list[dict[str, Any]] = []

    if isinstance(content_blocks, str):
        content_str = content_blocks.strip()
        if content_str.startswith(("[", "{")):
            try:
                content_blocks = json.loads(content_str)
            except Exception:
                pass

    if isinstance(content_blocks, list):
        for item in content_blocks:
            if isinstance(item, dict):
                s_title = item.get("title", "")
                s_content = item.get("content", [])
                if isinstance(s_content, str):
                    s_content = [s_content]
                slides_data.append({"title": s_title, "bullets": s_content})
            elif isinstance(item, str):
                slides_data.append({"title": "", "raw": item})
    elif isinstance(content_blocks, dict):
        s_title = content_blocks.get("title", title)
        s_content = content_blocks.get("content", [])
        if isinstance(s_content, str):
            s_content = [s_content]
        slides_data.append({"title": s_title, "bullets": s_content})

    if not slides_data:
        raw_input = str(content_blocks or "")
        if "--" in raw_input:
            raw_slides = [s.strip() for s in raw_input.split("--") if s.strip()]
        else:
            raw_slides = [
                s.strip()
                for s in re.split(r"(?i)(?=(?:Folie|Slide)\s*\d+:?)", raw_input)
                if s.strip()
            ]
        for slide_text in raw_slides:
            slides_data.append({"title": "", "raw": slide_text})

    existing_pages = doc.body.get_draw_pages()
    start_idx = len(existing_pages) + 1

    for idx, slide_info in enumerate(slides_data):
        page_num = start_idx + idx
        page = DrawPage(f"page{page_num}")

        if "raw" in slide_info:
            slide_title, bullet_points = _parse_slide_text(
                slide_info["raw"], default_title=f"Folie {page_num}"
            )
        else:
            slide_title = slide_info.get("title") or f"Folie {page_num}"
            bullet_points = slide_info.get("bullets", [])

        page.append(_create_slide_title_frame(slide_title))
        if bullet_points:
            page.append(_create_slide_outline_frame(bullet_points))

        doc.body.append(page)


def create_odp_presentation(title: str, content_blocks: Any) -> bytes:
    """Creates an ODP presentation document and returns its binary content."""
    doc = Document("presentation")
    doc.body.clear()
    append_odp_slides(doc, title, content_blocks)
    return _document_to_bytes(doc)


def read_odp_presentation(doc: Document) -> str:
    """Extracts text content and headers from an ODP presentation."""
    return doc.get_formatted_text().strip()


# ==========================================
# MAIN TOOL ENTRYPOINT
# ==========================================

def manage_odf(
    file_storage_service: FileStorageService,
    action: ActionType = "create",
    doc_type: DocType = "odt",
    filename: str = "document.odt",
    title: str = "",
    content: Any = None,
    conversation_id: str | None = None,
    base_dir: str | Path | None = None,
    **kwargs: Any,
) -> dict[str, Any] | str:
    """
    Tool to create, read, append to, or update OpenDocument Format files (.odt, .ods, .odp).
    """
    target_base = Path(base_dir or ".").resolve()
    effective_content = _extract_effective_content(content, kwargs)

    logger.debug(
        "Executing manage_odf: action=%s, doc_type=%s, filename=%s",
        action,
        doc_type,
        filename,
    )

    if not filename.lower().endswith(f".{doc_type}"):
        filename = f"{Path(filename).stem}.{doc_type}"

    try:
        def _save_and_respond(file_bytes: bytes, target_doc_type: str) -> dict[str, Any]:
            saved_path = file_storage_service.write_sandboxed_file(
                file_path=filename,
                content=file_bytes,
                base_dir=str(target_base),
                sandbox_id=conversation_id,
            )
            return {
                "status": "success",
                "filename": filename,
                "file_path": saved_path,
                "doc_type": target_doc_type,
                "is_attachment": True,
            }

        match action:
            case "create":
                match doc_type:
                    case "odt":
                        file_bytes = create_odt_document(title, effective_content)
                    case "ods":
                        file_bytes = create_ods_spreadsheet(title, effective_content)
                    case "odp":
                        file_bytes = create_odp_presentation(title, effective_content)
                    case _:
                        return f"Error: Unsupported document type '{doc_type}'."

                return _save_and_respond(file_bytes, doc_type)

            case "append" | "update":
                target_path = locate_file(filename, target_base, conversation_id)
                if not target_path or not target_path.is_file():
                    return manage_odf(
                        file_storage_service=file_storage_service,
                        action="create",
                        doc_type=doc_type,
                        filename=filename,
                        title=title,
                        content=effective_content,
                        conversation_id=conversation_id,
                        base_dir=base_dir,
                        **kwargs,
                    )

                doc = Document(target_path)
                ext = target_path.suffix.lower().lstrip(".")
                effective_doc_type = ext if ext in SUPPORTED_DOC_TYPES else doc_type

                match effective_doc_type:
                    case "odt":
                        append_odt_content(doc.body, effective_content)
                        file_bytes = _document_to_bytes(doc)
                    case "ods":
                        file_bytes = append_ods_spreadsheet(doc, effective_content)
                    case "odp":
                        append_odp_slides(doc, title, effective_content)
                        file_bytes = _document_to_bytes(doc)
                    case _:
                        return f"Error: Append not supported for doc_type '{effective_doc_type}'."

                return _save_and_respond(file_bytes, effective_doc_type)

            case "read":
                target_path = locate_file(filename, target_base, conversation_id)
                if not target_path or not target_path.is_file():
                    return f"Error: ODF file '{filename}' was not found in workspace."

                doc = Document(target_path)
                ext = target_path.suffix.lower().lstrip(".")
                effective_doc_type = ext if ext in SUPPORTED_DOC_TYPES else doc_type

                match effective_doc_type:
                    case "odt":
                        text_content = read_odt_document(doc)
                    case "ods":
                        text_content = read_ods_spreadsheet(doc)
                    case "odp":
                        text_content = read_odp_presentation(doc)
                    case _:
                        text_content = doc.get_formatted_text().strip()

                return f"=== ODF DOCUMENT CONTENT ({filename}) ===\n\n{text_content}"

            case _:
                return (
                    f"Error: Unknown action '{action}'. "
                    "Supported actions: 'create', 'read', 'append', 'update'."
                )

    except Exception as exc:
        logger.error("Error executing manage_odf for file '%s': %s", filename, exc, exc_info=True)
        return f"Error executing manage_odf: {exc}"
