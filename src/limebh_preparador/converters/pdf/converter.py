from __future__ import annotations

from collections.abc import Iterator

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from limebh_preparador.application.progress import notify_progress
from limebh_preparador.contracts.pdf import PdfPage, build_pdf_document_record
from limebh_preparador.converters.base import ConversionContext
from limebh_preparador.converters.pdf.extractor import (
    MAX_ENCODED_PAGE_CONTENT_BYTES,
    encoded_page_content_size,
    extract_embedded_files,
    extract_outline,
    extract_page_images,
)
from limebh_preparador.core.cleaning import UnicodeSanitizer


class PdfDocumentConverter:
    converter_id = "pdf_document"
    record_type = "pdf_document"
    supported_extensions = frozenset({".pdf"})

    def convert(self, context: ConversionContext) -> Iterator[dict[str, object]]:
        if context.source.suffix.lower() != ".pdf":
            raise ValueError(f"Extensão PDF não suportada: {context.source.suffix}")

        context.cancellation_token.raise_if_cancelled()
        reader = PdfReader(context.source, strict=False)
        warnings: list[str] = []
        if reader.is_encrypted:
            try:
                password_type = reader.decrypt("")
            except Exception as error:
                raise PdfReadError("O PDF é protegido por senha") from error
            if not password_type:
                raise PdfReadError("O PDF é protegido por senha")
            warnings.append("pdf_decrypted_with_empty_password")

        sanitizer = context.unicode_sanitizer or UnicodeSanitizer()
        metadata = reader.metadata
        title = (
            sanitizer.clean(str(metadata.title).strip()) if metadata and metadata.title else None
        )
        author = (
            sanitizer.clean(str(metadata.author).strip()) if metadata and metadata.author else None
        )

        pages: list[PdfPage] = []
        images = []
        page_count = len(reader.pages)
        for page_number, page in enumerate(reader.pages, start=1):
            context.cancellation_token.raise_if_cancelled()
            text = ""
            method = "none"
            encoded_size = encoded_page_content_size(page)
            if encoded_size is not None and encoded_size > MAX_ENCODED_PAGE_CONTENT_BYTES:
                warnings.append(f"page_{page_number:04d}_content_stream_too_large")
            else:
                try:
                    extracted = page.extract_text(extraction_mode="layout") or ""
                    text = sanitizer.clean(extracted).strip()
                    if text:
                        method = "embedded_text"
                    else:
                        warnings.append(f"page_{page_number:04d}_no_extractable_text")
                except Exception:
                    warnings.append(f"page_{page_number:04d}_text_extraction_failed")
            pages.append(
                PdfPage(
                    page_number=page_number,
                    text=text,
                    extraction_method=method,  # type: ignore[arg-type]
                )
            )
            images.extend(extract_page_images(page, page_number, warnings))
            notify_progress(context.progress_callback, "converting", page_number, page_count)

        context.cancellation_token.raise_if_cancelled()
        outline = extract_outline(reader, warnings)
        embedded_files = extract_embedded_files(reader, warnings)
        yield build_pdf_document_record(
            source_file=context.source.name,
            source_size_bytes=context.source_size_bytes,
            pages=pages,
            title=title,
            author=author,
            outline=outline,
            embedded_files=embedded_files,
            images=images,
            converted_at=context.converted_at,
            warnings=warnings,
        )
