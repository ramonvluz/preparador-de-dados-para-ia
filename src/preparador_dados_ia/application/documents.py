from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from preparador_dados_ia.application.conversion import ConversionSettings
from preparador_dados_ia.application.output_setup import prepare_output
from preparador_dados_ia.application.progress import ProgressCallback, notify_progress
from preparador_dados_ia.converters.base import ConversionContext, RecordConverter
from preparador_dados_ia.core.cancellation import CancellationToken, ConversionCancelled
from preparador_dados_ia.core.cleaning import UnicodeSanitizer, sanitize_record
from preparador_dados_ia.core.partitioning import PartitionLimits
from preparador_dados_ia.outputs.artifacts import (
    write_document_readme,
    write_pdf_readme,
    write_report,
    write_word_readme,
)
from preparador_dados_ia.outputs.markdown import MarkdownDocumentWriter
from preparador_dados_ia.outputs.pdf_markdown import PdfMarkdownWriter
from preparador_dados_ia.outputs.word_markdown import WordMarkdownWriter


def convert_document(
    input_path: Path,
    output_dir: Path,
    *,
    converter: RecordConverter,
    detected_format: str,
    settings: ConversionSettings | None = None,
    cancellation_token: CancellationToken | None = None,
    progress_callback: ProgressCallback | None = None,
    started_at: datetime | None = None,
) -> dict[str, object]:
    """Converte uma fonte narrativa registrada para Markdown particionado."""

    settings = settings or ConversionSettings()
    cancellation_token = cancellation_token or CancellationToken()
    input_path = input_path.resolve()
    output_dir = output_dir.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    source_stat = input_path.stat()
    started_at = started_at or datetime.now(UTC)
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=UTC)

    ready_dir = prepare_output(output_dir)
    limits = PartitionLimits(max_bytes=settings.max_bytes, max_tokens=settings.max_tokens)
    if converter.record_type == "text_document":
        writer: MarkdownDocumentWriter | PdfMarkdownWriter | WordMarkdownWriter = (
            MarkdownDocumentWriter(
                ready_dir,
                limits,
            )
        )
    elif converter.record_type == "pdf_document":
        writer = PdfMarkdownWriter(ready_dir, limits)
    elif converter.record_type == "word_document":
        writer = WordMarkdownWriter(ready_dir, limits)
    else:
        raise ValueError(f"Não há gravador Markdown para {converter.record_type}")
    sanitizer = UnicodeSanitizer()
    total = converted = failed = segmented = oversized = 0
    warning_count = heading_count = section_count = 0
    encoding: str | None = None
    pdf_page_count = pdf_pages_with_text = pdf_pages_without_text = 0
    pdf_outline_count = embedded_file_count = image_count = 0
    ocr_applied = False
    word_block_count = word_paragraph_count = word_heading_count = 0
    word_list_count = word_table_count = word_section_count = 0
    word_images_omitted = 0
    word_headers_footers_omitted = False
    word_features_omitted: list[str] = []
    word_suspicious_text_sequences = 0
    word_inferred_headings = 0
    word_inferred_table_headers = 0
    document_metadata: dict[str, object] = {}
    pdf_catalog: dict[str, object] = {}
    errors: list[dict[str, object]] = []
    cancelled = False
    notify_progress(progress_callback, "preparing", 0, 1)

    context = ConversionContext(
        source=input_path,
        source_size_bytes=source_stat.st_size,
        converted_at=started_at,
        cancellation_token=cancellation_token,
        progress_callback=progress_callback,
        unicode_sanitizer=sanitizer,
        options={"profile": settings.profile.value},
    )
    try:
        for record in converter.convert(context):
            cancellation_token.raise_if_cancelled()
            total += 1
            if record.get("record_type") != converter.record_type:
                raise ValueError("O conversor produziu um tipo de registro incompatível")
            sanitized = sanitize_record(record, sanitizer)
            if not isinstance(sanitized, dict):
                raise TypeError("O registro normalizado não é um objeto")

            data = sanitized.get("data")
            processing = sanitized.get("processing")
            if isinstance(data, dict):
                document_metadata = {
                    "title": data.get("title"),
                    "author": data.get("author"),
                }
                encoding_value = data.get("encoding")
                encoding = str(encoding_value) if encoding_value else encoding
                headings = data.get("headings")
                sections = data.get("sections")
                heading_count += len(headings) if isinstance(headings, list) else 0
                section_count += len(sections) if isinstance(sections, list) else 0
                pages = data.get("pages")
                if isinstance(pages, list):
                    pdf_page_count += len(pages)
                    page_with_text_count = sum(
                        1
                        for page in pages
                        if isinstance(page, dict) and bool(str(page.get("text") or "").strip())
                    )
                    pdf_pages_with_text += page_with_text_count
                    pdf_pages_without_text += len(pages) - page_with_text_count
                outline = data.get("outline")
                if isinstance(outline, list):
                    pdf_outline_count += _outline_item_count(outline)
                embedded_files = data.get("embedded_files")
                images = data.get("images")
                if converter.record_type == "pdf_document":
                    pdf_catalog = {
                        "outline": outline or [],
                        "embedded_files": embedded_files or [],
                        "images": images or [],
                    }
                embedded_file_count += (
                    len(embedded_files) if isinstance(embedded_files, list) else 0
                )
                image_count += len(images) if isinstance(images, list) else 0
                blocks = data.get("blocks")
                if isinstance(blocks, list):
                    word_block_count += len(blocks)
                    for block in blocks:
                        if not isinstance(block, dict):
                            continue
                        block_type = block.get("type")
                        if block_type == "paragraph":
                            word_paragraph_count += 1
                        elif block_type == "heading":
                            word_heading_count += 1
                        elif block_type == "list_item":
                            word_list_count += 1
                        elif block_type == "table":
                            word_table_count += 1
                    word_section_count += len(sections) if isinstance(sections, list) else 0
            if isinstance(processing, dict):
                warnings = processing.get("warnings")
                if isinstance(warnings, list):
                    warning_count += len(warnings)
                ocr_applied = bool(processing.get("ocr_applied", False))
                word_images_omitted = int(processing.get("images_omitted", 0) or 0)
                word_headers_footers_omitted = bool(
                    processing.get("headers_footers_omitted", False)
                )
                omitted = processing.get("features_omitted")
                if isinstance(omitted, list):
                    word_features_omitted = [str(feature) for feature in omitted]
                word_suspicious_text_sequences += int(
                    processing.get("suspicious_text_sequences", 0) or 0
                )
                word_inferred_headings += int(processing.get("inferred_headings", 0) or 0)
                word_inferred_table_headers += int(processing.get("inferred_table_headers", 0) or 0)

            segment_count, remains_oversized = writer.add(sanitized, cancellation_token)
            if segment_count > 1:
                segmented += 1
                warning_count += 1
            if remains_oversized:
                oversized += 1
                warning_count += 1
            converted += 1
    except ConversionCancelled:
        cancelled = True
    except Exception as error:
        failed += 1
        total = max(total, 1)
        errors.append(
            {
                "record_number": total,
                "stage": "extract_normalize_and_write",
                "error_type": type(error).__name__,
            }
        )

    notify_progress(progress_callback, "writing", converted, total)
    finished_at = datetime.now(UTC)
    if cancelled:
        result = "cancelled"
    elif converted == 0 and failed > 0:
        result = "failure"
    elif failed or warning_count or segmented or oversized:
        result = "success_with_warnings"
    else:
        result = "success"

    generated_files = [
        *(f"PRONTO_PARA_IA/{part.file}" for part in writer.parts),
        "LEIA-ME.txt",
        "relatorio_conversao.json",
    ]
    report: dict[str, object] = {
        "conversion_id": f"conversion_{uuid4().hex}",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": max(0.0, (finished_at - started_at).total_seconds()),
        "sources": [
            {
                "file_name": input_path.name,
                "size_bytes": source_stat.st_size,
                "modified_at": datetime.fromtimestamp(source_stat.st_mtime, tz=UTC).isoformat(),
                "detected_format": detected_format,
                "contract": f"{converter.record_type}@1.0",
            }
        ],
        "profile": settings.profile.value,
        "output_format": "markdown",
        "settings": {
            "max_size_mb": settings.max_size_mb,
            "max_bytes": settings.max_bytes,
            "max_tokens": settings.max_tokens,
            "token_estimator": "conservative_utf8_bytes_divided_by_2",
            "unicode_cleanup": True,
        },
        "unit_label": "documento",
        "total_records": total,
        "converted_records": converted,
        "failed_records": failed,
        "segmented_records": segmented,
        "oversized_records": oversized,
        "warnings_count": warning_count,
        "unicode_cleanup": sanitizer.report(),
        "parts": [part.as_dict() for part in writer.parts],
        "errors": errors,
        "generated_files": generated_files,
        "result": result,
    }

    if converter.record_type == "pdf_document":
        report["document_metadata"] = document_metadata
        report["pdf_catalog"] = pdf_catalog
        report["pdf_extraction"] = {
            "page_count": pdf_page_count,
            "pages_with_text": pdf_pages_with_text,
            "pages_without_text": pdf_pages_without_text,
            "outline_items": pdf_outline_count,
            "embedded_files_catalogued": embedded_file_count,
            "images_catalogued": image_count,
            "ocr_applied": ocr_applied,
        }
        report["omitted_content"] = {
            "embedded_file_binaries": embedded_file_count,
            "image_binaries": image_count,
            "ocr_not_applied": not ocr_applied,
            "external_references_downloaded": False,
        }
    elif converter.record_type == "word_document":
        report["document_metadata"] = document_metadata
        report["word_extraction"] = {
            "block_count": word_block_count,
            "paragraphs": word_paragraph_count,
            "headings": word_heading_count,
            "list_items": word_list_count,
            "tables": word_table_count,
            "sections": word_section_count,
            "inferred_headings": word_inferred_headings,
            "inferred_table_headers": word_inferred_table_headers,
        }
        report["text_quality"] = {
            "suspected_encoding_corruption": bool(word_suspicious_text_sequences),
            "suspicious_sequences": word_suspicious_text_sequences,
            "automatic_text_repair_applied": False,
        }
        report["omitted_content"] = {
            "images": word_images_omitted,
            "headers_footers": word_headers_footers_omitted,
            "advanced_features": word_features_omitted,
            "external_references_downloaded": False,
        }
    else:
        report["document_metadata"] = document_metadata
        report["text_extraction"] = {
            "encoding": encoding,
            "headings_detected": heading_count,
            "sections_detected": section_count,
        }
        report["omitted_content"] = {
            "binary_attachments": 0,
            "external_references_downloaded": False,
        }

    if converter.record_type == "pdf_document":
        write_pdf_readme(
            output_dir,
            source_name=input_path.name,
            converted_records=converted,
            part_count=len(writer.parts),
            page_count=pdf_page_count,
            pages_without_text=pdf_pages_without_text,
            embedded_file_count=embedded_file_count,
            image_count=image_count,
            cancelled=cancelled,
        )
    elif converter.record_type == "word_document":
        write_word_readme(
            output_dir,
            source_name=input_path.name,
            converted_records=converted,
            part_count=len(writer.parts),
            block_count=word_block_count,
            section_count=word_section_count,
            table_count=word_table_count,
            image_count=word_images_omitted,
            headers_footers_omitted=word_headers_footers_omitted,
            features_omitted=word_features_omitted,
            suspicious_text_sequences=word_suspicious_text_sequences,
            inferred_headings=word_inferred_headings,
            inferred_table_headers=word_inferred_table_headers,
            cancelled=cancelled,
        )
    else:
        write_document_readme(
            output_dir,
            source_name=input_path.name,
            source_type=detected_format,
            converted_records=converted,
            part_count=len(writer.parts),
            encoding=encoding,
            cancelled=cancelled,
        )
    write_report(output_dir, report)
    notify_progress(
        progress_callback,
        "cancelled" if cancelled else "completed",
        converted,
        total,
    )
    return report


def _outline_item_count(items: list[object]) -> int:
    count = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        count += 1
        children = item.get("children")
        if isinstance(children, list):
            count += _outline_item_count(children)
    return count
