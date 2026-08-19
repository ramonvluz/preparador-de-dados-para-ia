from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from preparador_dados_ia.contracts.common import build_document_record

RECORD_TYPE = "text_document"
TextFileType = Literal["txt", "markdown"]


@dataclass(frozen=True, slots=True)
class TextHeading:
    level: int
    text: str
    line_number: int

    def __post_init__(self) -> None:
        if self.level < 1 or self.line_number < 1:
            raise ValueError("Nível e linha do título devem ser positivos")

    def as_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "text": self.text,
            "line_number": self.line_number,
        }


@dataclass(frozen=True, slots=True)
class TextSection:
    title: str | None
    level: int | None
    content: str
    start_line: int
    end_line: int

    def __post_init__(self) -> None:
        if self.level is not None and self.level < 1:
            raise ValueError("O nível da seção deve ser positivo")
        if self.start_line < 1 or self.end_line < self.start_line:
            raise ValueError("O intervalo de linhas da seção é inválido")

    def as_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "level": self.level,
            "content": self.content,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }


def build_text_document_record(
    *,
    source_file: str,
    source_file_type: TextFileType,
    source_size_bytes: int,
    encoding: str,
    content: str,
    title: str | None = None,
    headings: Sequence[TextHeading] = (),
    sections: Sequence[TextSection] = (),
    converted_at: datetime | None = None,
    warnings: list[str] | None = None,
    unicode_cleaned: bool = True,
) -> dict[str, object]:
    if source_file_type not in {"txt", "markdown"}:
        raise ValueError("Tipo de arquivo textual não suportado")
    if not encoding:
        raise ValueError("A codificação detectada é obrigatória")

    data = {
        "title": title,
        "encoding": encoding,
        "content_format": "markdown" if source_file_type == "markdown" else "plain_text",
        "content": content,
        "headings": [heading.as_dict() for heading in headings],
        "sections": [section.as_dict() for section in sections],
    }
    return build_document_record(
        record_type=RECORD_TYPE,
        record_prefix="text",
        source_file=source_file,
        source_file_type=source_file_type,
        source_size_bytes=source_size_bytes,
        data=data,
        converted_at=converted_at,
        warnings=warnings,
        unicode_cleaned=unicode_cleaned,
    )
