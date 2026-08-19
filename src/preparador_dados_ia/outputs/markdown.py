from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from preparador_dados_ia.core.cancellation import CancellationToken
from preparador_dados_ia.core.partitioning import PartitionLimits, estimate_tokens
from preparador_dados_ia.outputs.atomic import atomic_write_text

SETEXT_UNDERLINE = re.compile(r"^\s*(={3,}|-{3,})\s*$")


@dataclass(frozen=True, slots=True)
class MarkdownPartInfo:
    file: str
    records: int
    estimated_tokens: int
    size_bytes: int
    content_line_start: int
    content_line_end: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class MarkdownDocumentWriter:
    """Representa `text_document` em partes Markdown autossuficientes."""

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
        self.parts: list[MarkdownPartInfo] = []

    def add(
        self,
        record: dict[str, object],
        cancellation_token: CancellationToken,
    ) -> tuple[int, bool]:
        body = _markdown_body(record)
        full = _render_part(record, body, 1, _line_end(body), None, None)
        if _fits(full, self.limits):
            chunks = [(0, len(body))]
            remains_oversized = False
        else:
            chunks, remains_oversized = _split_body(record, body, self.limits)

        segment_count = len(chunks)
        for segment_number, (start, end) in enumerate(chunks, start=1):
            cancellation_token.raise_if_cancelled()
            piece = body[start:end]
            line_start = body.count("\n", 0, start) + 1
            line_end = line_start + piece.count("\n")
            if piece.endswith("\n") and line_end > line_start:
                line_end -= 1
            rendered = _render_part(
                record,
                piece,
                line_start,
                max(line_start, line_end),
                segment_number if segment_count > 1 else None,
                segment_count if segment_count > 1 else None,
            )
            if not _fits(rendered, self.limits):
                remains_oversized = True
            self._write_part(rendered, line_start, max(line_start, line_end))
        return segment_count, remains_oversized

    def _write_part(self, content: str, line_start: int, line_end: int) -> None:
        filename = f"{self.file_prefix}_parte_{len(self.parts) + 1:04d}.md"
        path = self.output_dir / filename
        atomic_write_text(path, content)
        self.parts.append(
            MarkdownPartInfo(
                file=filename,
                records=1,
                estimated_tokens=estimate_tokens(content),
                size_bytes=path.stat().st_size,
                content_line_start=line_start,
                content_line_end=line_end,
            )
        )


def _markdown_body(record: dict[str, object]) -> str:
    if record.get("record_type") != "text_document":
        raise ValueError("O gravador Markdown recebeu um contrato incompatível")
    data = record.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("content"), str):
        raise TypeError("O contrato textual não contém conteúdo válido")

    content = data["content"]
    if data.get("content_format") == "markdown":
        return content

    headings = data.get("headings")
    heading_by_line: dict[int, tuple[int, str]] = {}
    if isinstance(headings, list):
        for heading in headings:
            if not isinstance(heading, dict):
                continue
            line_number = heading.get("line_number")
            level = heading.get("level")
            text = heading.get("text")
            if isinstance(line_number, int) and isinstance(level, int) and isinstance(text, str):
                heading_by_line[line_number] = (level, text)

    output: list[str] = []
    lines = content.splitlines()
    for line_number, line in enumerate(lines, start=1):
        heading = heading_by_line.get(line_number)
        if heading is not None:
            level, text = heading
            output.append(f"{'#' * min(max(level, 1), 6)} {text}")
            continue
        if line_number > 1 and line_number - 1 in heading_by_line and SETEXT_UNDERLINE.match(line):
            continue
        output.append(line)
    return "\n".join(output) + ("\n" if content.endswith(("\n", "\r")) else "")


def _render_part(
    record: dict[str, object],
    body: str,
    line_start: int,
    line_end: int,
    segment_number: int | None,
    segment_count: int | None,
) -> str:
    source = record.get("source")
    if not isinstance(source, dict):
        raise TypeError("Envelope textual incompleto")

    provenance = f"> Fonte: {source.get('file_name') or 'não informada'}"
    if segment_number is not None and segment_count is not None:
        provenance += f" — parte {segment_number}/{segment_count} (linhas {line_start}–{line_end})"
    return f"{provenance}\n\n{body.rstrip()}\n"


def _fits(content: str, limits: PartitionLimits) -> bool:
    return (
        len(content.encode("utf-8")) <= limits.max_bytes
        and estimate_tokens(content) <= limits.max_tokens
    )


def _split_body(
    record: dict[str, object],
    body: str,
    limits: PartitionLimits,
) -> tuple[list[tuple[int, int]], bool]:
    chunks: list[tuple[int, int]] = []
    position = 0
    remains_oversized = False
    while position < len(body):
        low, high, best = 1, len(body) - position, 0
        while low <= high:
            middle = (low + high) // 2
            candidate = body[position : position + middle]
            line_start = body.count("\n", 0, position) + 1
            rendered = _render_part(
                record,
                candidate,
                line_start,
                line_start + candidate.count("\n"),
                len(chunks) + 1,
                999_999,
            )
            if _fits(rendered, limits):
                best = middle
                low = middle + 1
            else:
                high = middle - 1

        if best == 0:
            chunks.append((position, len(body)))
            remains_oversized = True
            break
        length = _preferred_break(body, position, best)
        chunks.append((position, position + length))
        position += length
    if not chunks:
        chunks.append((0, 0))
        remains_oversized = True
    return chunks, remains_oversized


def _preferred_break(body: str, position: int, maximum: int) -> int:
    window = body[position : position + maximum]
    minimum = maximum // 2
    for separator in ("\n\n", "\n", " "):
        index = window.rfind(separator)
        boundary = index + len(separator)
        if index >= 0 and boundary >= minimum:
            return boundary
    return maximum


def _line_end(body: str) -> int:
    if not body:
        return 1
    return max(1, len(body.splitlines()))
