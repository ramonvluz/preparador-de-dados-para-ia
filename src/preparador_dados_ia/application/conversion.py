from __future__ import annotations

import mailbox
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from preparador_dados_ia.application.output_setup import prepare_output
from preparador_dados_ia.application.progress import (
    ProgressCallback,
    notify_progress,
)
from preparador_dados_ia.converters.email import message_to_record
from preparador_dados_ia.core.cancellation import CancellationToken, ConversionCancelled
from preparador_dados_ia.core.cleaning import UnicodeSanitizer, sanitize_record
from preparador_dados_ia.core.partitioning import PartitionLimits, split_oversized_record
from preparador_dados_ia.outputs.ai_ready import compact_email_record
from preparador_dados_ia.outputs.artifacts import write_readme, write_report
from preparador_dados_ia.outputs.parts import OutputFormat, PartWriter


class DestinationProfile(StrEnum):
    PLATFORM = "platform"
    API = "api"


@dataclass(frozen=True, slots=True)
class ConversionSettings:
    profile: DestinationProfile = DestinationProfile.PLATFORM
    max_size_mb: float = 50.0
    max_tokens: int = 500_000
    include_html: bool = False

    def __post_init__(self) -> None:
        if self.max_size_mb <= 0 or self.max_tokens <= 0:
            raise ValueError("Os limites de tamanho e tokens devem ser maiores que zero.")

    @property
    def max_bytes(self) -> int:
        return int(self.max_size_mb * 1024 * 1024)

    @property
    def output_format(self) -> OutputFormat:
        if self.profile is DestinationProfile.API:
            return OutputFormat.JSONL
        return OutputFormat.JSON


def _append_record_warning(record: dict[str, object], warning: str) -> dict[str, object]:
    updated = dict(record)
    processing = dict(updated.get("processing") or {})
    processing["warnings"] = list(processing.get("warnings") or []) + [warning]
    updated["processing"] = processing
    return updated


def convert_mbox(
    input_path: Path,
    output_dir: Path,
    *,
    settings: ConversionSettings | None = None,
    cancellation_token: CancellationToken | None = None,
    progress_callback: ProgressCallback | None = None,
    started_at: datetime | None = None,
) -> dict[str, object]:
    """Converte um MBOX incrementalmente e gera somente artefatos finais."""

    settings = settings or ConversionSettings()
    cancellation_token = cancellation_token or CancellationToken()
    input_path = input_path.resolve()
    output_dir = output_dir.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Arquivo MBOX não encontrado: {input_path}")

    source_stat = input_path.stat()
    started_at = started_at or datetime.now(UTC)
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=UTC)

    ready_dir = prepare_output(output_dir)
    writer = PartWriter(
        ready_dir,
        PartitionLimits(max_bytes=settings.max_bytes, max_tokens=settings.max_tokens),
        settings.output_format,
    )
    sanitizer = UnicodeSanitizer()
    total = converted = failed = 0
    segmented_messages = oversized_messages = attachment_count = 0
    errors: list[dict[str, object]] = []
    cancelled = False
    notify_progress(progress_callback, "preparing", 0)

    mbox = mailbox.mbox(input_path, create=False)
    try:
        for index, message in enumerate(mbox, start=1):
            cancellation_token.raise_if_cancelled()
            total += 1
            try:
                record = message_to_record(
                    message,
                    source_file=input_path.name,
                    source_size_bytes=source_stat.st_size,
                    include_html=settings.include_html,
                    converted_at=started_at,
                )
                sanitized = sanitize_record(record, sanitizer)
                if not isinstance(sanitized, dict):
                    raise TypeError("O registro normalizado não é um objeto.")

                data = sanitized.get("data")
                if isinstance(data, dict) and isinstance(data.get("attachments"), list):
                    attachment_count += len(data["attachments"])

                records, remains_oversized = split_oversized_record(
                    sanitized,
                    writer.single_record_limits,
                )
                if len(records) > 1:
                    segmented_messages += 1
                if remains_oversized:
                    oversized_messages += 1
                    records = [
                        _append_record_warning(item, "record_exceeds_partition_limits")
                        for item in records
                    ]
                for item in records:
                    writer.add(compact_email_record(item))
                converted += 1
            except Exception as error:
                failed += 1
                errors.append(
                    {
                        "message_number": index,
                        "stage": "normalize_and_partition",
                        "error_type": type(error).__name__,
                    }
                )
            notify_progress(progress_callback, "converting", index)
    except ConversionCancelled:
        cancelled = True
    finally:
        mbox.close()
        notify_progress(progress_callback, "writing", converted, total)
        writer.flush()

    finished_at = datetime.now(UTC)
    if cancelled:
        result = "cancelled"
    elif converted == 0 and failed > 0:
        result = "failure"
    elif failed or segmented_messages or oversized_messages:
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
                "modified_at": datetime.fromtimestamp(
                    source_stat.st_mtime,
                    tz=UTC,
                ).isoformat(),
                "detected_format": "mbox",
                "contract": "email_message@1.0",
            }
        ],
        "profile": settings.profile.value,
        "output_format": settings.output_format.value,
        "settings": {
            "max_size_mb": settings.max_size_mb,
            "max_bytes": settings.max_bytes,
            "max_tokens": settings.max_tokens,
            "token_estimator": "conservative_utf8_bytes_divided_by_2",
            "include_html": settings.include_html,
            "unicode_cleanup": True,
        },
        "total_messages": total,
        "converted_messages": converted,
        "failed_messages": failed,
        "segmented_messages": segmented_messages,
        "oversized_messages": oversized_messages,
        "unit_label": "mensagem",
        "total_records": total,
        "converted_records": converted,
        "failed_records": failed,
        "segmented_records": segmented_messages,
        "oversized_records": oversized_messages,
        "attachments_catalogued": attachment_count,
        "unicode_cleanup": sanitizer.report(),
        "parts": [part.as_dict() for part in writer.parts],
        "errors": errors,
        "omitted_content": {
            "attachment_binaries": attachment_count,
            "attachment_content_extracted": False,
        },
        "generated_files": generated_files,
        "result": result,
    }

    write_readme(
        output_dir,
        source_name=input_path.name,
        converted_messages=converted,
        part_count=len(writer.parts),
        attachment_count=attachment_count,
        output_format=settings.output_format,
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
