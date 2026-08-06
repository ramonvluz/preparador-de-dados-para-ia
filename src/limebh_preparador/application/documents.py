from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from limebh_preparador.application.conversion import ConversionSettings
from limebh_preparador.application.output_setup import prepare_output
from limebh_preparador.application.progress import ProgressCallback, notify_progress
from limebh_preparador.converters.base import ConversionContext, RecordConverter
from limebh_preparador.core.cancellation import CancellationToken, ConversionCancelled
from limebh_preparador.core.cleaning import UnicodeSanitizer, sanitize_record
from limebh_preparador.core.partitioning import PartitionLimits
from limebh_preparador.outputs.artifacts import write_document_readme, write_report
from limebh_preparador.outputs.markdown import MarkdownDocumentWriter


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
    writer = MarkdownDocumentWriter(
        ready_dir,
        PartitionLimits(max_bytes=settings.max_bytes, max_tokens=settings.max_tokens),
    )
    sanitizer = UnicodeSanitizer()
    total = converted = failed = segmented = oversized = 0
    warning_count = heading_count = section_count = 0
    encoding: str | None = None
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
        for index, record in enumerate(converter.convert(context), start=1):
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
                encoding_value = data.get("encoding")
                encoding = str(encoding_value) if encoding_value else encoding
                headings = data.get("headings")
                sections = data.get("sections")
                heading_count += len(headings) if isinstance(headings, list) else 0
                section_count += len(sections) if isinstance(sections, list) else 0
            if isinstance(processing, dict) and isinstance(processing.get("warnings"), list):
                warning_count += len(processing["warnings"])

            segment_count, remains_oversized = writer.add(sanitized, cancellation_token)
            if segment_count > 1:
                segmented += 1
                warning_count += 1
            if remains_oversized:
                oversized += 1
                warning_count += 1
            converted += 1
            notify_progress(progress_callback, "converting", index, 1)
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
                "absolute_path": str(input_path),
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
        "text_extraction": {
            "encoding": encoding,
            "headings_detected": heading_count,
            "sections_detected": section_count,
        },
        "unicode_cleanup": sanitizer.report(),
        "parts": [part.as_dict() for part in writer.parts],
        "errors": errors,
        "omitted_content": {
            "binary_attachments": 0,
            "external_references_downloaded": False,
        },
        "generated_files": generated_files,
        "result": result,
    }

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
