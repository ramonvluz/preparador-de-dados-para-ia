from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from preparador_dados_ia.contracts.common import build_document_record

RECORD_TYPE = "word_document"


@dataclass(frozen=True, slots=True)
class WordParagraph:
    text: str
    style: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {"type": "paragraph", "text": self.text, "style": self.style}


@dataclass(frozen=True, slots=True)
class WordHeading:
    text: str
    level: int
    inferred: bool = False

    def __post_init__(self) -> None:
        if self.level < 1:
            raise ValueError("O nível do título deve ser positivo")

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {"type": "heading", "text": self.text, "level": self.level}
        if self.inferred:
            result["inferred"] = True
        return result


@dataclass(frozen=True, slots=True)
class WordListItem:
    text: str
    level: int
    ordered: bool

    def __post_init__(self) -> None:
        if self.level < 0:
            raise ValueError("O nível do item de lista não pode ser negativo")

    def as_dict(self) -> dict[str, object]:
        return {
            "type": "list_item",
            "text": self.text,
            "level": self.level,
            "ordered": self.ordered,
        }


@dataclass(frozen=True, slots=True)
class WordTable:
    rows: tuple[tuple[str, ...], ...]
    has_header: bool
    header_inferred: bool = False

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "type": "table",
            "rows": [list(row) for row in self.rows],
            "has_header": self.has_header,
        }
        if self.header_inferred:
            result["header_inferred"] = True
        return result


WordBlock = WordParagraph | WordHeading | WordListItem | WordTable


@dataclass(frozen=True, slots=True)
class WordSection:
    """Intervalo inclusivo de blocos associado a um título do documento."""

    title: str
    level: int
    start_block: int
    end_block: int

    def __post_init__(self) -> None:
        if self.level < 1:
            raise ValueError("O nível da seção deve ser positivo")
        if self.start_block < 0 or self.end_block < self.start_block:
            raise ValueError("O intervalo de blocos da seção é inválido")

    def as_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "level": self.level,
            "start_block": self.start_block,
            "end_block": self.end_block,
        }


def build_word_document_record(
    *,
    source_file: str,
    source_size_bytes: int,
    blocks: Sequence[WordBlock],
    title: str | None = None,
    author: str | None = None,
    sections: Sequence[WordSection] = (),
    converted_at: datetime | None = None,
    warnings: list[str] | None = None,
    unicode_cleaned: bool = True,
    images_omitted: int = 0,
    headers_footers_omitted: bool = False,
    features_omitted: Sequence[str] = (),
    suspicious_text_sequences: int = 0,
    inferred_headings: int = 0,
    inferred_table_headers: int = 0,
) -> dict[str, object]:
    if images_omitted < 0:
        raise ValueError("A quantidade de imagens omitidas não pode ser negativa")
    if min(suspicious_text_sequences, inferred_headings, inferred_table_headers) < 0:
        raise ValueError("As métricas de qualidade do DOCX não podem ser negativas")
    data = {
        "title": title,
        "author": author,
        "sections": [section.as_dict() for section in sections],
        "blocks": [block.as_dict() for block in blocks],
    }
    return build_document_record(
        record_type=RECORD_TYPE,
        record_prefix="word",
        source_file=source_file,
        source_file_type="docx",
        source_size_bytes=source_size_bytes,
        data=data,
        converted_at=converted_at,
        warnings=warnings,
        unicode_cleaned=unicode_cleaned,
        processing={
            "images_omitted": images_omitted,
            "headers_footers_omitted": headers_footers_omitted,
            "features_omitted": list(features_omitted),
            "suspicious_text_sequences": suspicious_text_sequences,
            "inferred_headings": inferred_headings,
            "inferred_table_headers": inferred_table_headers,
        },
    )
