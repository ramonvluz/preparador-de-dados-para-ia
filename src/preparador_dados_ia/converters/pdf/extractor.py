from __future__ import annotations

import re
from collections.abc import Iterable

from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject

from preparador_dados_ia.contracts.pdf import PdfEmbeddedFile, PdfImage, PdfOutlineItem

MAX_ENCODED_PAGE_CONTENT_BYTES = 32 * 1024 * 1024


def extract_outline(
    reader: PdfReader,
    warnings: list[str],
) -> list[PdfOutlineItem]:
    try:
        items = reader.outline
    except Exception:
        warnings.append("pdf_outline_read_failed")
        return []
    return _outline_items(reader, items, warnings)


def _outline_items(
    reader: PdfReader,
    items: Iterable[object],
    warnings: list[str],
) -> list[PdfOutlineItem]:
    output: list[PdfOutlineItem] = []
    for item in items:
        if isinstance(item, list):
            children = _outline_items(reader, item, warnings)
            if output and children:
                parent = output[-1]
                output[-1] = PdfOutlineItem(
                    title=parent.title,
                    page_number=parent.page_number,
                    children=parent.children + tuple(children),
                )
            elif children:
                output.extend(children)
            continue

        title = _outline_title(item)
        if not title:
            warnings.append("pdf_outline_item_without_title")
            continue
        try:
            page_index = reader.get_destination_page_number(item)  # type: ignore[arg-type]
            page_number = page_index + 1 if page_index >= 0 else None
        except Exception:
            page_number = None
            warnings.append("pdf_outline_destination_unresolved")
        output.append(PdfOutlineItem(title=title, page_number=page_number))
    return output


def _outline_title(item: object) -> str:
    title = getattr(item, "title", None)
    if title is None and isinstance(item, dict):
        title = item.get("/Title")
    return str(title or "").strip()


def extract_embedded_files(
    reader: PdfReader,
    warnings: list[str],
) -> list[PdfEmbeddedFile]:
    output: list[PdfEmbeddedFile] = []
    try:
        attachments = reader.attachment_list
        for attachment in attachments:
            try:
                subtype = attachment.subtype
                media_type = _decode_pdf_name(str(subtype).removeprefix("/")) if subtype else None
                size = attachment.size
                output.append(
                    PdfEmbeddedFile(
                        file_name=str(attachment.alternative_name or attachment.name),
                        media_type=media_type,
                        size_bytes=int(size) if size is not None else None,
                    )
                )
            except Exception:
                warnings.append("pdf_embedded_file_catalog_failed")
    except Exception:
        warnings.append("pdf_embedded_files_read_failed")
    return output


def extract_page_images(
    page: DictionaryObject,
    page_number: int,
    warnings: list[str],
) -> list[PdfImage]:
    images: list[PdfImage] = []
    try:
        resources = page.get("/Resources")
        if resources is None:
            return images
        _catalog_images(
            resources.get_object(),
            page_number,
            images,
            set(),
        )
    except Exception:
        warnings.append(f"page_{page_number:04d}_image_catalog_failed")
    return images


def _catalog_images(
    resources: DictionaryObject,
    page_number: int,
    images: list[PdfImage],
    visited: set[tuple[int, int] | int],
) -> None:
    xobjects_reference = resources.get("/XObject")
    if xobjects_reference is None:
        return
    xobjects = xobjects_reference.get_object()
    for name in sorted(xobjects, key=str):
        reference = xobjects[name]
        reference_key = _reference_key(reference)
        if reference_key in visited:
            continue
        visited.add(reference_key)
        item = reference.get_object()
        subtype = str(item.get("/Subtype") or "")
        if subtype == "/Image":
            images.append(
                PdfImage(
                    page_number=page_number,
                    image_number=len(images) + 1,
                    media_type=_image_media_type(item.get("/Filter")),
                    width=_positive_int(item.get("/Width")),
                    height=_positive_int(item.get("/Height")),
                )
            )
        elif subtype == "/Form":
            nested_resources = item.get("/Resources")
            if nested_resources is not None:
                _catalog_images(
                    nested_resources.get_object(),
                    page_number,
                    images,
                    visited,
                )


def encoded_page_content_size(page: DictionaryObject) -> int | None:
    """Retorna o tamanho codificado sem descompactar o fluxo de conteúdo."""

    contents = page.get("/Contents")
    if contents is None:
        return 0
    references = contents if isinstance(contents, ArrayObject) else [contents]
    total = 0
    try:
        for reference in references:
            stream = reference.get_object()
            raw = getattr(stream, "_data", None)
            if not isinstance(raw, bytes):
                return None
            total += len(raw)
    except Exception:
        return None
    return total


def _reference_key(reference: object) -> tuple[int, int] | int:
    idnum = getattr(reference, "idnum", None)
    generation = getattr(reference, "generation", None)
    if isinstance(idnum, int) and isinstance(generation, int):
        return idnum, generation
    return id(reference)


def _positive_int(value: object) -> int | None:
    try:
        number = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _image_media_type(filter_value: object) -> str | None:
    values = filter_value if isinstance(filter_value, ArrayObject) else [filter_value]
    filters = {str(value) for value in values if value is not None}
    if "/DCTDecode" in filters:
        return "image/jpeg"
    if "/JPXDecode" in filters:
        return "image/jp2"
    if "/CCITTFaxDecode" in filters:
        return "image/tiff"
    if "/JBIG2Decode" in filters:
        return "image/jbig2"
    if filters:
        return "application/octet-stream"
    return None


def _decode_pdf_name(value: str) -> str:
    return re.sub(
        r"#([0-9A-Fa-f]{2})",
        lambda match: chr(int(match.group(1), 16)),
        value,
    )
