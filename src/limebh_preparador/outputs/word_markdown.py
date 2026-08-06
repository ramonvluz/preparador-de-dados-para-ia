from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from limebh_preparador.core.cancellation import CancellationToken
from limebh_preparador.core.partitioning import PartitionLimits, estimate_tokens
from limebh_preparador.outputs.atomic import atomic_write_text


@dataclass(frozen=True, slots=True)
class WordMarkdownPartInfo:
    file: str
    records: int
    estimated_tokens: int
    size_bytes: int
    block_start: int | None
    block_end: int | None
    block_segments: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class _WordUnit:
    kind: str
    text: str
    block_start: int | None = None
    block_end: int | None = None
    segment_number: int | None = None
    segment_count: int | None = None


class WordMarkdownWriter:
    """Representa `word_document` em Markdown, preservando blocos estruturais."""

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
        self.parts: list[WordMarkdownPartInfo] = []

    def add(
        self,
        record: dict[str, object],
        cancellation_token: CancellationToken,
    ) -> tuple[int, bool]:
        expanded: list[_WordUnit] = []
        remains_oversized = False
        for unit in _word_units(record):
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

    def _write_part(self, content: str, units: list[_WordUnit]) -> None:
        filename = f"{self.file_prefix}_parte_{len(self.parts) + 1:04d}.md"
        path = self.output_dir / filename
        atomic_write_text(path, content)
        starts = [unit.block_start for unit in units if unit.block_start is not None]
        ends = [unit.block_end for unit in units if unit.block_end is not None]
        self.parts.append(
            WordMarkdownPartInfo(
                file=filename,
                records=1,
                estimated_tokens=estimate_tokens(content),
                size_bytes=path.stat().st_size,
                block_start=min(starts) if starts else None,
                block_end=max(ends) if ends else None,
                block_segments=len(starts),
            )
        )


def _word_units(record: dict[str, object]) -> list[_WordUnit]:
    if record.get("record_type") != "word_document":
        raise ValueError("O gravador Word recebeu um contrato incompatível")
    data = record.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("blocks"), list):
        raise TypeError("O contrato Word não contém blocos válidos")

    units = [_WordUnit(kind="catalog", text=_catalog_markdown(data))]
    list_lines: list[str] = []
    list_start: int | None = None

    def flush_list(end: int) -> None:
        nonlocal list_lines, list_start
        if list_start is not None:
            units.append(
                _WordUnit(
                    kind="list",
                    text="\n".join(list_lines),
                    block_start=list_start,
                    block_end=end,
                )
            )
        list_lines = []
        list_start = None

    for index, block in enumerate(data["blocks"]):
        if not isinstance(block, dict):
            raise TypeError("Bloco Word inválido")
        block_type = block.get("type")
        if block_type == "list_item":
            if list_start is None:
                list_start = index
            list_lines.append(_list_item_markdown(block))
            continue
        flush_list(index - 1)
        if block_type == "heading":
            level = block.get("level")
            text = block.get("text")
            if not isinstance(level, int) or not isinstance(text, str):
                raise TypeError("Título Word incompleto")
            markdown = f"{'#' * min(max(level, 1), 6)} {text}"
        elif block_type == "paragraph":
            text = block.get("text")
            if not isinstance(text, str):
                raise TypeError("Parágrafo Word incompleto")
            style = str(block.get("style") or "")
            if style == "Title":
                markdown = f"# {text}"
            elif style == "Subtitle":
                markdown = f"_{text}_"
            else:
                markdown = text
        elif block_type == "table":
            markdown = _table_markdown(block)
        else:
            raise ValueError(f"Tipo de bloco Word não suportado: {block_type}")
        units.append(
            _WordUnit(
                kind=str(block_type),
                text=markdown,
                block_start=index,
                block_end=index,
            )
        )
    flush_list(len(data["blocks"]) - 1)
    return units


def _catalog_markdown(data: dict[str, object]) -> str:
    title = str(data.get("title") or "Documento Word")
    author = str(data.get("author") or "não informado")
    blocks = data.get("blocks")
    sections = data.get("sections")
    block_count = len(blocks) if isinstance(blocks, list) else 0
    section_count = len(sections) if isinstance(sections, list) else 0
    return "\n".join(
        [
            "## Catálogo do documento Word",
            "",
            f"- Título: {title}",
            f"- Autor: {author}",
            f"- Blocos estruturais: {block_count}",
            f"- Seções detectadas: {section_count}",
        ]
    )


def _list_item_markdown(block: dict[str, object]) -> str:
    text = block.get("text")
    level = block.get("level")
    ordered = block.get("ordered")
    if not isinstance(text, str) or not isinstance(level, int) or not isinstance(ordered, bool):
        raise TypeError("Item de lista Word incompleto")
    marker = "1." if ordered else "-"
    clean_text = text.replace("\r", " ").replace("\n", " ")
    return f"{'    ' * max(level, 0)}{marker} {clean_text}"


def _table_markdown(block: dict[str, object]) -> str:
    rows = block.get("rows")
    has_header = block.get("has_header")
    if not isinstance(rows, list) or not isinstance(has_header, bool):
        raise TypeError("Tabela Word incompleta")
    valid_rows = [row for row in rows if isinstance(row, list)]
    column_count = max((len(row) for row in valid_rows), default=0)
    if column_count == 0:
        return "_Tabela vazia._"

    normalized = [
        [_table_cell(row[index] if index < len(row) else "") for index in range(column_count)]
        for row in valid_rows
    ]
    if has_header and normalized:
        header = normalized[0]
        body = normalized[1:]
    else:
        header = [f"Coluna {index}" for index in range(1, column_count + 1)]
        body = normalized
    lines = [
        f"| {' | '.join(header)} |",
        f"| {' | '.join('---' for _ in range(column_count))} |",
    ]
    lines.extend(f"| {' | '.join(row)} |" for row in body)
    return "\n".join(lines)


def _table_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


def _split_unit(
    record: dict[str, object],
    unit: _WordUnit,
    limits: PartitionLimits,
) -> tuple[list[_WordUnit], bool]:
    if _fits(_render_part(record, [unit], 999_999, 999_999), limits):
        return [unit], False
    if unit.kind == "table":
        table_chunks = _split_table_unit(record, unit, limits)
        if table_chunks is not None:
            return table_chunks, False
    return _split_text_unit(record, unit, limits)


def _split_table_unit(
    record: dict[str, object],
    unit: _WordUnit,
    limits: PartitionLimits,
) -> list[_WordUnit] | None:
    lines = unit.text.splitlines()
    if len(lines) <= 2:
        return None
    header = lines[:2]
    rows = lines[2:]
    pieces: list[str] = []
    position = 0
    while position < len(rows):
        low, high, best = 1, len(rows) - position, 0
        while low <= high:
            middle = (low + high) // 2
            text = "\n".join([*header, *rows[position : position + middle]])
            candidate = replace(
                unit,
                text=text,
                segment_number=len(pieces) + 1,
                segment_count=999_999,
            )
            if _fits(_render_part(record, [candidate], 999_999, 999_999), limits):
                best = middle
                low = middle + 1
            else:
                high = middle - 1
        if best == 0:
            return None
        pieces.append("\n".join([*header, *rows[position : position + best]]))
        position += best
    count = len(pieces)
    return [
        replace(unit, text=piece, segment_number=index, segment_count=count)
        for index, piece in enumerate(pieces, start=1)
    ]


def _split_text_unit(
    record: dict[str, object],
    unit: _WordUnit,
    limits: PartitionLimits,
) -> tuple[list[_WordUnit], bool]:
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
    return (
        [
            replace(unit, text=piece, segment_number=index, segment_count=count)
            for index, piece in enumerate(pieces, start=1)
        ],
        remains_oversized,
    )


def _group_units(
    record: dict[str, object],
    units: list[_WordUnit],
    limits: PartitionLimits,
) -> list[list[_WordUnit]]:
    groups: list[list[_WordUnit]] = []
    current: list[_WordUnit] = []
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
    units: list[_WordUnit],
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
        raise TypeError("Envelope Word incompleto")

    starts = [unit.block_start for unit in units if unit.block_start is not None]
    ends = [unit.block_end for unit in units if unit.block_end is not None]
    segmented = any(unit.segment_count is not None for unit in units)
    warnings = list(processing.get("warnings") or [])
    if segmented:
        warnings.append("oversized_word_unit_segmented")
    metadata: list[tuple[str, object]] = [
        ("schema_version", record.get("schema_version")),
        ("record_type", record.get("record_type")),
        ("record_id", record.get("record_id")),
        ("source_file", source.get("file_name")),
        ("source_type", source.get("file_type")),
        ("source_size_bytes", source.get("size_bytes")),
        ("title", data.get("title")),
        ("author", data.get("author")),
        ("total_block_count", len(data.get("blocks") or [])),
        ("section_count", len(data.get("sections") or [])),
        ("block_start", min(starts) if starts else None),
        ("block_end", max(ends) if ends else None),
        ("part_number", part_number),
        ("part_count", part_count),
        ("converted_at", processing.get("converted_at")),
        ("unicode_cleaned", processing.get("unicode_cleaned")),
        ("images_omitted", processing.get("images_omitted", 0)),
        ("headers_footers_omitted", processing.get("headers_footers_omitted", False)),
        ("features_omitted", processing.get("features_omitted", [])),
        ("warnings", warnings),
    ]
    header = "\n".join(f"{key}: {_yaml_scalar(value)}" for key, value in metadata)
    body = "\n\n".join(_render_unit(unit) for unit in units)
    return f"---\n{header}\n---\n\n{body.rstrip()}\n"


def _render_unit(unit: _WordUnit) -> str:
    segment = (
        f" segment={unit.segment_number}/{unit.segment_count}"
        if unit.segment_number is not None and unit.segment_count is not None
        else ""
    )
    if unit.kind == "catalog":
        return f"<!-- LIMEBH_WORD_CATALOG{segment} -->\n\n{unit.text.rstrip()}"
    start = unit.block_start if unit.block_start is not None else 0
    end = unit.block_end if unit.block_end is not None else start
    return (
        f"<!-- LIMEBH_WORD_BLOCK_START start={start} end={end}{segment} -->\n\n"
        f"{unit.text.rstrip()}\n\n"
        f"<!-- LIMEBH_WORD_BLOCK_END start={start} end={end}{segment} -->"
    )


def _yaml_scalar(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


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
