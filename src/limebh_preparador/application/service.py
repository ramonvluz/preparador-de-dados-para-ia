from __future__ import annotations

from datetime import datetime
from pathlib import Path

from limebh_preparador.application.conversion import ConversionSettings, convert_mbox
from limebh_preparador.application.documents import convert_document
from limebh_preparador.application.progress import ProgressCallback
from limebh_preparador.converters.pdf import PdfDocumentConverter
from limebh_preparador.converters.registry import ConverterRegistry
from limebh_preparador.converters.text import TextDocumentConverter
from limebh_preparador.core.cancellation import CancellationToken

MBOX_EXTENSION = ".mbox"
PDF_EXTENSION = ".pdf"
TEXT_EXTENSIONS = TextDocumentConverter.supported_extensions
SUPPORTED_SOURCE_EXTENSIONS = frozenset({MBOX_EXTENSION, PDF_EXTENSION, *TEXT_EXTENSIONS})


def build_default_registry() -> ConverterRegistry:
    registry = ConverterRegistry()
    registry.register(TextDocumentConverter())
    registry.register(PdfDocumentConverter())
    return registry


def convert_source(
    input_path: Path,
    output_dir: Path,
    *,
    settings: ConversionSettings | None = None,
    cancellation_token: CancellationToken | None = None,
    progress_callback: ProgressCallback | None = None,
    started_at: datetime | None = None,
) -> dict[str, object]:
    suffix = input_path.suffix.lower()
    common = {
        "settings": settings,
        "cancellation_token": cancellation_token,
        "progress_callback": progress_callback,
        "started_at": started_at,
    }
    if suffix == MBOX_EXTENSION:
        return convert_mbox(input_path, output_dir, **common)

    registry = build_default_registry()
    converter = registry.resolve(input_path)
    return convert_document(
        input_path,
        output_dir,
        converter=converter,
        detected_format=source_format_id(input_path),
        **common,
    )


def source_format_id(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".mbox":
        return "mbox"
    if suffix == ".txt":
        return "txt"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".pdf":
        return "pdf"
    return suffix.removeprefix(".") or "unknown"


def source_format_label(path: Path) -> str:
    return {"mbox": "MBOX", "txt": "TXT", "markdown": "Markdown", "pdf": "PDF"}.get(
        source_format_id(path),
        "Desconhecido",
    )


def source_unit_label(path: Path, *, plural: bool = False) -> str:
    if path.suffix.lower() == MBOX_EXTENSION:
        return "mensagens" if plural else "mensagem"
    if path.suffix.lower() == PDF_EXTENSION:
        return "páginas" if plural else "página"
    return "documentos" if plural else "documento"
