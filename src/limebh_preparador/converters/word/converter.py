from __future__ import annotations

from collections.abc import Iterator

from docx import Document

from limebh_preparador.application.progress import notify_progress
from limebh_preparador.contracts.word import build_word_document_record
from limebh_preparador.converters.base import ConversionContext
from limebh_preparador.converters.word.extractor import (
    document_author,
    document_title,
    embedded_image_count,
    extract_blocks,
    has_header_footer_content,
    omitted_features,
    validate_docx_archive,
)
from limebh_preparador.core.cleaning import UnicodeSanitizer


class WordDocumentConverter:
    converter_id = "word_document"
    record_type = "word_document"
    supported_extensions = frozenset({".docx"})

    def convert(self, context: ConversionContext) -> Iterator[dict[str, object]]:
        if context.source.suffix.lower() != ".docx":
            raise ValueError(f"Extensão DOCX não suportada: {context.source.suffix}")

        context.cancellation_token.raise_if_cancelled()
        archive_names = validate_docx_archive(context.source)
        document = Document(context.source)
        sanitizer = context.unicode_sanitizer or UnicodeSanitizer()
        blocks, sections = extract_blocks(
            document,
            sanitizer,
            context.cancellation_token,
            lambda current, total: notify_progress(
                context.progress_callback,
                "converting",
                current,
                total,
            ),
        )
        images_omitted = embedded_image_count(document)
        headers_footers_omitted = has_header_footer_content(document)
        features_omitted = omitted_features(archive_names, document)
        warnings: list[str] = []
        if images_omitted:
            warnings.append(f"word_images_omitted:{images_omitted}")
        if headers_footers_omitted:
            warnings.append("word_headers_footers_omitted")
        warnings.extend(f"word_feature_omitted:{feature}" for feature in features_omitted)
        if not blocks:
            warnings.append("word_document_without_extractable_blocks")

        context.cancellation_token.raise_if_cancelled()
        yield build_word_document_record(
            source_file=context.source.name,
            source_size_bytes=context.source_size_bytes,
            title=document_title(document, sanitizer),
            author=document_author(document, sanitizer),
            blocks=blocks,
            sections=sections,
            converted_at=context.converted_at,
            warnings=warnings,
            images_omitted=images_omitted,
            headers_footers_omitted=headers_footers_omitted,
            features_omitted=features_omitted,
        )
