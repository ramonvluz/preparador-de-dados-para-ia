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
from preparador_dados_ia.core.partitioning import PartitionLimits, record_metrics
from preparador_dados_ia.outputs.ai_ready import compact_tabular_record
from preparador_dados_ia.outputs.artifacts import (
    write_report,
    write_spreadsheet_readme,
    write_tabular_readme,
)
from preparador_dados_ia.outputs.parts import PartWriter


def convert_tabular(
    input_path: Path,
    output_dir: Path,
    *,
    converter: RecordConverter,
    settings: ConversionSettings | None = None,
    cancellation_token: CancellationToken | None = None,
    progress_callback: ProgressCallback | None = None,
    started_at: datetime | None = None,
) -> dict[str, object]:
    """Converte uma fonte tabular registrada para JSON ou JSONL particionado."""

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
    writer = PartWriter(
        ready_dir,
        limits,
        settings.output_format,
        filename_prefix="dados",
    )
    sanitizer = UnicodeSanitizer()
    source_format = input_path.suffix.lower().removeprefix(".")
    total_rows = converted_rows = segment_count = oversized = 0
    column_count = ragged_rows = blank_rows_skipped = 0
    sheet_count = table_count = formula_count = 0
    merged_ranges = hidden_rows = hidden_columns = 0
    encoding: str | None = None
    delimiter: str | None = None
    has_header: bool | None = None
    warnings: set[str] = set()
    errors: list[dict[str, object]] = []
    seen_datasets: set[tuple[object, ...]] = set()
    dataset_catalog: list[dict[str, object]] = []
    dataset_segment_counts: dict[tuple[object, ...], int] = {}
    seen_sheets: set[object] = set()
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
            if record.get("record_type") != converter.record_type:
                raise ValueError("O conversor produziu um tipo de registro incompatível")
            sanitized = sanitize_record(record, sanitizer)
            if not isinstance(sanitized, dict):
                raise TypeError("O registro normalizado não é um objeto")

            data = sanitized.get("data")
            processing = sanitized.get("processing")
            dataset = data.get("dataset") if isinstance(data, dict) else None
            rows = dataset.get("rows") if isinstance(dataset, dict) else None
            columns = dataset.get("columns") if isinstance(dataset, dict) else None
            row_count = len(rows) if isinstance(rows, list) else 0
            converted_rows += row_count
            column_count = max(column_count, len(columns) if isinstance(columns, list) else 0)
            has_header = (
                bool(dataset.get("has_header")) if isinstance(dataset, dict) else has_header
            )
            if isinstance(data, dict):
                workbook = data.get("workbook")
                sheet = data.get("sheet")
                sheet_index = sheet.get("index") if isinstance(sheet, dict) else None
                sheet_count = max(
                    sheet_count,
                    int(workbook.get("sheet_count", 0)) if isinstance(workbook, dict) else 0,
                )
                dataset_key = (
                    sheet_index,
                    dataset.get("name") if isinstance(dataset, dict) else None,
                    dataset.get("reference") if isinstance(dataset, dict) else None,
                )
                dataset_segment_counts[dataset_key] = dataset_segment_counts.get(dataset_key, 0) + 1
                if isinstance(dataset, dict) and dataset_key not in seen_datasets:
                    seen_datasets.add(dataset_key)
                    total_rows += int(dataset.get("total_rows", 0) or 0)
                    catalog_entry: dict[str, object] = {
                        "name": dataset.get("name"),
                        "source_kind": dataset.get("source_kind"),
                        "reference": dataset.get("reference"),
                        "has_header": dataset.get("has_header"),
                        "total_rows": dataset.get("total_rows"),
                        "columns": dataset.get("columns") or [],
                    }
                    if isinstance(sheet, dict):
                        catalog_entry["sheet"] = {
                            "index": sheet.get("index"),
                            "name": sheet.get("name"),
                            "visibility": sheet.get("visibility"),
                            "used_range": sheet.get("used_range"),
                        }
                    dataset_catalog.append(catalog_entry)
                    if dataset.get("source_kind") == "excel_table":
                        table_count += 1
                formulas = data.get("formulas")
                if isinstance(formulas, list):
                    formula_count += len(formulas)
                encoding = str(data.get("encoding") or encoding or "") or None
                dialect = data.get("dialect")
                if isinstance(dialect, dict):
                    delimiter = str(dialect.get("delimiter") or delimiter or "") or None
            if isinstance(processing, dict):
                warnings.update(str(item) for item in processing.get("warnings", []))
                ragged_rows = int(processing.get("ragged_rows", ragged_rows) or 0)
                blank_rows_skipped = int(
                    processing.get("blank_rows_skipped", blank_rows_skipped) or 0
                )
                sheet = data.get("sheet") if isinstance(data, dict) else None
                sheet_index = sheet.get("index") if isinstance(sheet, dict) else None
                if sheet_index is not None and sheet_index not in seen_sheets:
                    seen_sheets.add(sheet_index)
                    merged_ranges += int(processing.get("merged_ranges", 0) or 0)
                    hidden_rows += int(processing.get("hidden_rows", 0) or 0)
                    hidden_columns += int(processing.get("hidden_columns", 0) or 0)

            ready_record = compact_tabular_record(sanitized)
            _, record_bytes, record_tokens = record_metrics(ready_record)
            if record_bytes > writer.single_record_limits.max_bytes or (
                record_tokens > writer.single_record_limits.max_tokens
            ):
                oversized += 1
                warnings.add("tabular_segment_exceeds_configured_limit")
            writer.add(ready_record)
            segment_count += 1
    except ConversionCancelled:
        cancelled = True
    except Exception as error:
        errors.append(
            {
                "record_number": segment_count + 1,
                "stage": "extract_normalize_and_write",
                "error_type": type(error).__name__,
            }
        )
    writer.flush()

    notify_progress(progress_callback, "writing", converted_rows, total_rows)
    finished_at = datetime.now(UTC)
    failed = len(errors)
    if cancelled:
        result = "cancelled"
    elif failed and converted_rows == 0:
        result = "failure"
    elif failed or warnings or oversized:
        result = "success_with_warnings"
    else:
        result = "success"
    parts = [_tabular_part(part.as_dict()) for part in writer.parts]
    generated_files = [
        *(f"PRONTO_PARA_IA/{part['file']}" for part in parts),
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
                "detected_format": source_format,
                "contract": f"{converter.record_type}@1.0",
            }
        ],
        "profile": settings.profile.value,
        "output_format": settings.output_format.value,
        "settings": {
            "max_size_mb": settings.max_size_mb,
            "max_bytes": settings.max_bytes,
            "max_tokens": settings.max_tokens,
            "token_estimator": "conservative_utf8_bytes_divided_by_2",
            "unicode_cleanup": True,
        },
        "unit_label": "linha",
        "total_records": total_rows,
        "converted_records": converted_rows,
        "failed_records": failed,
        "segmented_records": sum(count > 1 for count in dataset_segment_counts.values()),
        "oversized_records": oversized,
        "warnings_count": len(warnings),
        "dataset_catalog": dataset_catalog,
        "unicode_cleanup": sanitizer.report(),
        "parts": parts,
        "errors": errors,
        "omitted_content": {"external_references_downloaded": False},
        "generated_files": generated_files,
        "result": result,
    }
    if source_format == "xlsx":
        report["spreadsheet_extraction"] = {
            "sheets": sheet_count,
            "datasets": len(seen_datasets),
            "tables": table_count,
            "columns_max": column_count,
            "rows": total_rows,
            "segments": segment_count,
            "formulas": formula_count,
            "merged_ranges": merged_ranges,
            "hidden_rows": hidden_rows,
            "hidden_columns": hidden_columns,
            "external_links_followed": False,
        }
        write_spreadsheet_readme(
            output_dir,
            source_name=input_path.name,
            converted_rows=converted_rows,
            sheet_count=sheet_count,
            dataset_count=len(seen_datasets),
            table_count=table_count,
            formula_count=formula_count,
            part_count=len(parts),
            output_format=settings.output_format,
            cancelled=cancelled,
        )
    else:
        report["tabular_extraction"] = {
            "encoding": encoding,
            "delimiter": delimiter,
            "has_header": has_header,
            "columns": column_count,
            "rows": total_rows,
            "segments": segment_count,
            "ragged_rows_normalized": ragged_rows,
            "blank_rows_skipped": blank_rows_skipped,
        }
        write_tabular_readme(
            output_dir,
            source_name=input_path.name,
            converted_rows=converted_rows,
            column_count=column_count,
            part_count=len(parts),
            encoding=encoding,
            output_format=settings.output_format,
            cancelled=cancelled,
        )
    write_report(output_dir, report)
    notify_progress(
        progress_callback,
        "cancelled" if cancelled else "completed",
        converted_rows,
        total_rows,
    )
    return report


def _tabular_part(part: dict[str, object]) -> dict[str, object]:
    output = dict(part)
    output["records"] = output.pop("messages")
    output.pop("first_date", None)
    output.pop("last_date", None)
    return output
