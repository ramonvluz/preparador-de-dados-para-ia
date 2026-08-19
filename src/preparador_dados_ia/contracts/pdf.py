from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from preparador_dados_ia.contracts.common import build_document_record

RECORD_TYPE = "pdf_document"
PdfExtractionMethod = Literal["embedded_text", "ocr", "none"]


@dataclass(frozen=True, slots=True)
class PdfPage:
    page_number: int
    text: str
    extraction_method: PdfExtractionMethod

    def __post_init__(self) -> None:
        if self.page_number < 1:
            raise ValueError("O número da página deve ser positivo")
        if self.extraction_method not in {"embedded_text", "ocr", "none"}:
            raise ValueError("Método de extração de PDF inválido")

    def as_dict(self) -> dict[str, object]:
        return {
            "page_number": self.page_number,
            "text": self.text,
            "extraction_method": self.extraction_method,
        }


@dataclass(frozen=True, slots=True)
class PdfOutlineItem:
    title: str
    page_number: int | None = None
    children: tuple[PdfOutlineItem, ...] = ()

    def __post_init__(self) -> None:
        if self.page_number is not None and self.page_number < 1:
            raise ValueError("O número da página do sumário deve ser positivo")

    def as_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "page_number": self.page_number,
            "children": [item.as_dict() for item in self.children],
        }


@dataclass(frozen=True, slots=True)
class PdfEmbeddedFile:
    file_name: str
    media_type: str | None
    size_bytes: int | None

    def __post_init__(self) -> None:
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("O tamanho do arquivo incorporado não pode ser negativo")

    def as_dict(self) -> dict[str, object]:
        return {
            "file_name": self.file_name,
            "media_type": self.media_type,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class PdfImage:
    page_number: int
    image_number: int
    media_type: str | None
    width: int | None
    height: int | None

    def __post_init__(self) -> None:
        numeric_values = (self.page_number, self.image_number)
        optional_values = (self.width, self.height)
        if any(value < 1 for value in numeric_values):
            raise ValueError("Página e número da imagem devem ser positivos")
        if any(value is not None and value < 1 for value in optional_values):
            raise ValueError("As dimensões da imagem devem ser positivas")

    def as_dict(self) -> dict[str, object]:
        return {
            "page_number": self.page_number,
            "image_number": self.image_number,
            "media_type": self.media_type,
            "width": self.width,
            "height": self.height,
        }


def build_pdf_document_record(
    *,
    source_file: str,
    source_size_bytes: int,
    pages: Sequence[PdfPage],
    title: str | None = None,
    author: str | None = None,
    outline: Sequence[PdfOutlineItem] = (),
    embedded_files: Sequence[PdfEmbeddedFile] = (),
    images: Sequence[PdfImage] = (),
    converted_at: datetime | None = None,
    warnings: list[str] | None = None,
    unicode_cleaned: bool = True,
) -> dict[str, object]:
    page_data = [page.as_dict() for page in pages]
    data = {
        "title": title,
        "author": author,
        "page_count": len(page_data),
        "pages": page_data,
        "outline": [item.as_dict() for item in outline],
        "embedded_files": [item.as_dict() for item in embedded_files],
        "images": [image.as_dict() for image in images],
    }
    return build_document_record(
        record_type=RECORD_TYPE,
        record_prefix="pdf",
        source_file=source_file,
        source_file_type="pdf",
        source_size_bytes=source_size_bytes,
        data=data,
        converted_at=converted_at,
        warnings=warnings,
        unicode_cleaned=unicode_cleaned,
        processing={"ocr_applied": any(page.extraction_method == "ocr" for page in pages)},
    )
