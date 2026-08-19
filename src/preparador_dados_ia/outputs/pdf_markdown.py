from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from preparador_dados_ia.core.cancellation import CancellationToken
from preparador_dados_ia.core.partitioning import PartitionLimits, estimate_tokens
from preparador_dados_ia.outputs.atomic import atomic_write_text


@dataclass(frozen=True, slots=True)
class PdfMarkdownPartInfo:
    file: str
    records: int
    estimated_tokens: int
    size_bytes: int
    page_start: int | None
    page_end: int | None
    page_segments: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class _PdfUnit:
    kind: str
    text: str
    page_number: int | None = None
    extraction_method: str | None = None
    segment_number: int | None = None
    segment_count: int | None = None


class PdfMarkdownWriter:
    """Representa `pdf_document` em Markdown, preservando limites de página."""

    def __init__(
        self,
        output_dir: Path,
        limits: PartitionLimits,
        *,
        file_prefix: str = "documento",
    ) -> None:
        self.output_dir = output_dir
        self.limits = limits
        self.file_prefix = file_prefix
        self.parts: list[PdfMarkdownPartInfo] = []

    def add(
        self,
        record: dict[str, object],
        cancellation_token: CancellationToken,
    ) -> tuple[int, bool]:
        units = _pdf_units(record)
        expanded: list[_PdfUnit] = []
        remains_oversized = False
        for unit in units:
            chunks, unit_oversized = _split_unit(record, unit, self.limits)
            expanded.extend(chunks)
            remains_oversized = remains_oversized or unit_oversized

        groups = _group_units(record, expanded, self.limits)
        part_count = len(groups)
        for part_number, group in enumerate(groups, start=1):
            cancellation_token.raise_if_cancelled()
            rendered = _render_part(record, group, part_number, part_count)
            if not _fits(rendered, self.limits):
                remains_oversized = True
            self._write_part(rendered, group)
        return part_count, remains_oversized

    def _write_part(self, content: str, units: list[_PdfUnit]) -> None:
        filename = f"{self.file_prefix}_parte_{len(self.parts) + 1:04d}.md"
        path = self.output_dir / filename
        atomic_write_text(path, content)
        pages = [unit.page_number for unit in units if unit.page_number is not None]
        self.parts.append(
            PdfMarkdownPartInfo(
                file=filename,
                records=1,
                estimated_tokens=estimate_tokens(content),
                size_bytes=path.stat().st_size,
                page_start=min(pages) if pages else None,
                page_end=max(pages) if pages else None,
                page_segments=len(pages),
            )
        )


def _pdf_units(record: dict[str, object]) -> list[_PdfUnit]:
    if record.get("record_type") != "pdf_document":
        raise ValueError("O gravador PDF recebeu um contrato incompatível")
    data = record.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("pages"), list):
        raise TypeError("O contrato PDF não contém páginas válidas")

    units = [_PdfUnit(kind="catalog", text=_catalog_markdown(data))]
    for page in data["pages"]:
        if not isinstance(page, dict):
            raise TypeError("Página PDF inválida")
        page_number = page.get("page_number")
        text = page.get("text")
        extraction_method = page.get("extraction_method")
        if not isinstance(page_number, int) or not isinstance(text, str):
            raise TypeError("Página PDF incompleta")
        units.append(
            _PdfUnit(
                kind="page",
                text=text,
                page_number=page_number,
                extraction_method=str(extraction_method or "none"),
            )
        )
    return units


def _catalog_markdown(data: dict[str, object]) -> str:
    lines: list[str] = []
    title = data.get("title")
    if title:
        lines.extend([f"# {title}", ""])
    lines.extend(
        [
            "## Catálogo do PDF",
            "",
            f"- Autor: {data.get('author') or 'não informado'}",
            f"- Total de páginas: {data.get('page_count', 0)}",
        ]
    )

    outline = data.get("outline")
    if isinstance(outline, list) and outline:
        lines.extend(["", "### Sumário", ""])
        _outline_markdown(outline, lines, 0)

    embedded_files = data.get("embedded_files")
    if isinstance(embedded_files, list) and embedded_files:
        lines.extend(
            [
                "",
                "### Arquivos incorporados",
                "",
                "| Arquivo | Tipo | Tamanho (bytes) |",
                "|---|---|---:|",
            ]
        )
        for item in embedded_files:
            if isinstance(item, dict):
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _table_cell(item.get("file_name")),
                            _table_cell(item.get("media_type") or "não informado"),
                            _table_cell(item.get("size_bytes") or "não informado"),
                        ]
                    )
                    + " |"
                )

    images = data.get("images")
    if isinstance(images, list) and images:
        lines.extend(
            [
                "",
                "### Imagens catalogadas",
                "",
                "| Página | Imagem | Tipo | Dimensões |",
                "|---:|---:|---|---|",
            ]
        )
        for image in images:
            if not isinstance(image, dict):
                continue
            width = image.get("width")
            height = image.get("height")
            dimensions = f"{width} x {height}" if width and height else "não informadas"
            lines.append(
                "| "
                + " | ".join(
                    [
                        _table_cell(image.get("page_number")),
                        _table_cell(image.get("image_number")),
                        _table_cell(image.get("media_type") or "não informado"),
                        _table_cell(dimensions),
                    ]
                )
                + " |"
            )
    return "\n".join(lines).strip()


def _outline_markdown(items: list[object], lines: list[str], level: int) -> None:
    for item in items:
        if not isinstance(item, dict):
            continue
        page = item.get("page_number")
        page_label = f" (página {page})" if page else ""
        lines.append(f"{'  ' * level}- {item.get('title', '')}{page_label}")
        children = item.get("children")
        if isinstance(children, list):
            _outline_markdown(children, lines, level + 1)


def _split_unit(
    record: dict[str, object],
    unit: _PdfUnit,
    limits: PartitionLimits,
) -> tuple[list[_PdfUnit], bool]:
    if _fits(_render_part(record, [unit], 999_999, 999_999), limits):
        return [unit], False
    if not unit.text:
        return [unit], True

    pieces: list[str] = []
    position = 0
    remains_oversized = False
    while position < len(unit.text):
        low, high, best = 1, len(unit.text) - position, 0
        while low <= high:
            middle = (low + high) // 2
            candidate = replace(
                unit,
                text=unit.text[position : position + middle],
                segment_number=len(pieces) + 1,
                segment_count=999_999,
            )
            if _fits(_render_part(record, [candidate], 999_999, 999_999), limits):
                best = middle
                low = middle + 1
            else:
                high = middle - 1
        if best == 0:
            pieces.append(unit.text[position:])
            remains_oversized = True
            break
        length = _preferred_break(unit.text, position, best)
        pieces.append(unit.text[position : position + length])
        position += length

    count = len(pieces)
    return [
        replace(unit, text=piece, segment_number=index, segment_count=count)
        for index, piece in enumerate(pieces, start=1)
    ], remains_oversized


def _group_units(
    record: dict[str, object],
    units: list[_PdfUnit],
    limits: PartitionLimits,
) -> list[list[_PdfUnit]]:
    groups: list[list[_PdfUnit]] = []
    current: list[_PdfUnit] = []
    for unit in units:
        candidate = [*current, unit]
        if current and not _fits(
            _render_part(record, candidate, 999_999, 999_999),
            limits,
        ):
            groups.append(current)
            current = [unit]
        else:
            current = candidate
    if current:
        groups.append(current)
    return groups or [[]]


def _render_part(
    record: dict[str, object],
    units: list[_PdfUnit],
    part_number: int,
    part_count: int,
) -> str:
    source = record.get("source")
    data = record.get("data")
    processing = record.get("processing")
    if (
        not isinstance(source, dict)
        or not isinstance(data, dict)
        or not isinstance(processing, dict)
    ):
        raise TypeError("Envelope PDF incompleto")

    pages = [unit.page_number for unit in units if unit.page_number is not None]
    segmented = any(unit.segment_count is not None for unit in units)
    warnings = list(processing.get("warnings") or [])
    if segmented:
        warnings.append("oversized_pdf_unit_segmented")
    metadata: list[tuple[str, object]] = [
        ("schema_version", record.get("schema_version")),
        ("record_type", record.get("record_type")),
        ("record_id", record.get("record_id")),
        ("source_file", source.get("file_name")),
        ("source_type", source.get("file_type")),
        ("source_size_bytes", source.get("size_bytes")),
        ("title", data.get("title")),
        ("author", data.get("author")),
        ("total_page_count", data.get("page_count")),
        ("page_start", min(pages) if pages else None),
        ("page_end", max(pages) if pages else None),
        ("part_number", part_number),
        ("part_count", part_count),
        ("converted_at", processing.get("converted_at")),
        ("unicode_cleaned", processing.get("unicode_cleaned")),
        ("ocr_applied", processing.get("ocr_applied")),
        ("embedded_files_count", len(data.get("embedded_files") or [])),
        ("images_count", len(data.get("images") or [])),
        ("warnings", warnings),
    ]
    header = "\n".join(f"{key}: {_yaml_scalar(value)}" for key, value in metadata)
    body = "\n\n".join(_render_unit(unit) for unit in units)
    return f"---\n{header}\n---\n\n{body.rstrip()}\n"


def _render_unit(unit: _PdfUnit) -> str:
    segment = (
        f" segment={unit.segment_number}/{unit.segment_count}"
        if unit.segment_number is not None and unit.segment_count is not None
        else ""
    )
    if unit.kind == "catalog":
        return f"<!-- PREPARADOR_PDF_CATALOG{segment} -->\n\n{unit.text.rstrip()}"

    page_number = unit.page_number or 0
    if unit.text.strip():
        content = unit.text.strip()
    else:
        content = "_Nenhum texto incorporado foi extraído desta página. OCR não foi aplicado._"
    return (
        f"<!-- PREPARADOR_PAGE_START page={page_number}{segment} -->\n\n"
        f"## Página {page_number}\n\n"
        f"_Método de extração: `{unit.extraction_method}`._\n\n"
        f"{content}\n\n"
        f"<!-- PREPARADOR_PAGE_END page={page_number}{segment} -->"
    )


def _yaml_scalar(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _table_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _fits(content: str, limits: PartitionLimits) -> bool:
    return (
        len(content.encode("utf-8")) <= limits.max_bytes
        and estimate_tokens(content) <= limits.max_tokens
    )


def _preferred_break(content: str, position: int, maximum: int) -> int:
    window = content[position : position + maximum]
    minimum = maximum // 2
    for separator in ("\n\n", "\n", " "):
        index = window.rfind(separator)
        boundary = index + len(separator)
        if index >= 0 and boundary >= minimum:
            return boundary
    return maximum
