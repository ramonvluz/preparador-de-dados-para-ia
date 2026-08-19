from __future__ import annotations

from collections.abc import Iterator

from preparador_dados_ia.application.progress import notify_progress
from preparador_dados_ia.contracts.text import RECORD_TYPE, build_text_document_record
from preparador_dados_ia.converters.base import ConversionContext
from preparador_dados_ia.converters.text.reader import read_text_source
from preparador_dados_ia.converters.text.structure import analyze_text_structure
from preparador_dados_ia.core.cleaning import UnicodeSanitizer


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
        record = build_text_document_record(
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
        notify_progress(context.progress_callback, "converting", 1, 1)
        yield record
