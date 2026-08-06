from __future__ import annotations

from collections.abc import Iterator

from limebh_preparador.contracts.text import RECORD_TYPE, build_text_document_record
from limebh_preparador.converters.base import ConversionContext
from limebh_preparador.converters.text.reader import read_text_source
from limebh_preparador.converters.text.structure import analyze_text_structure
from limebh_preparador.core.cleaning import UnicodeSanitizer


class TextDocumentConverter:
    converter_id = "text_document"
    record_type = RECORD_TYPE
    supported_extensions = frozenset({".txt", ".md", ".markdown"})

    def convert(self, context: ConversionContext) -> Iterator[dict[str, object]]:
        suffix = context.source.suffix.lower()
        if suffix not in self.supported_extensions:
            raise ValueError(f"Extensão textual não suportada: {suffix}")

        decoded = read_text_source(context.source, context.cancellation_token)
        context.cancellation_token.raise_if_cancelled()
        sanitizer = context.unicode_sanitizer or UnicodeSanitizer()
        content = sanitizer.clean(decoded.content)
        is_markdown = suffix in {".md", ".markdown"}
        structure = analyze_text_structure(content, markdown=is_markdown)
        context.cancellation_token.raise_if_cancelled()
        yield build_text_document_record(
            source_file=context.source.name,
            source_file_type="markdown" if is_markdown else "txt",
            source_size_bytes=context.source_size_bytes,
            encoding=decoded.encoding,
            content=content,
            title=structure.title,
            headings=structure.headings,
            sections=structure.sections,
            converted_at=context.converted_at,
            warnings=list(decoded.warnings),
        )
