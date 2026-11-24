"""MIME-aware extraction for common Drive text and office-document formats."""
from __future__ import annotations

from html.parser import HTMLParser
from io import BytesIO
from typing import Iterable


class UnsupportedFileType(ValueError):
    pass


class _TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip_depth += 1
        elif tag.lower() in {"p", "br", "div", "li", "h1", "h2", "h3", "tr"} and not self._skip_depth:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        elif tag.lower() in {"p", "div", "li", "h1", "h2", "h3", "tr"} and not self._skip_depth:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data.strip():
            self.parts.append(data.strip())


def _decode(payload: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return payload.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return payload.decode("utf-8", errors="replace")


def _pdf_text(payload: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF support requires the pypdf dependency") from exc
    reader = PdfReader(BytesIO(payload))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _docx_text(payload: bytes) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("DOCX support requires python-docx") from exc
    doc = Document(BytesIO(payload))
    paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            paragraphs.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(paragraphs)


def _xlsx_text(payload: bytes) -> str:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("XLSX support requires openpyxl") from exc
    workbook = load_workbook(BytesIO(payload), read_only=True, data_only=True)
    lines: list[str] = []
    for sheet in workbook.worksheets:
        lines.append(f"Sheet: {sheet.title}")
        for row in sheet.iter_rows(values_only=True):
            values = [str(value) for value in row if value is not None and str(value).strip()]
            if values:
                lines.append(" | ".join(values))
    workbook.close()
    return "\n".join(lines)


def extract_text(payload: bytes, mime_type: str, filename: str = "") -> str:
    if not payload:
        return ""
    mime = (mime_type or "").lower().split(";")[0].strip()
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if mime == "application/pdf" or suffix == "pdf":
        text = _pdf_text(payload)
    elif mime in {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"} or suffix == "docx":
        text = _docx_text(payload)
    elif mime in {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"} or suffix == "xlsx":
        text = _xlsx_text(payload)
    elif mime in {"text/html", "application/xhtml+xml"} or suffix in {"html", "htm"}:
        parser = _TextHTMLParser()
        parser.feed(_decode(payload))
        text = " ".join(parser.parts)
    elif mime.startswith("text/") or suffix in {"txt", "md", "markdown", "csv", "tsv", "json", "jsonl", "xml", "yaml", "yml", "log"}:
        text = _decode(payload)
    else:
        raise UnsupportedFileType(f"Unsupported Drive file type: {mime or suffix or 'unknown'}")

    return "\n".join(line.strip() for line in text.splitlines() if line.strip()).strip()
