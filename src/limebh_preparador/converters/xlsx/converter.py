from __future__ import annotations

from collections.abc import Iterator

from limebh_preparador.application.progress import notify_progress
from limebh_preparador.contracts.tabular import (
    SPREADSHEET_RECORD_TYPE,
    TabularDatasetSegment,
    build_spreadsheet_workbook_record,
)
from limebh_preparador.converters.base import ConversionContext
from limebh_preparador.converters.xlsx.extractor import extract_workbook
from limebh_preparador.core.cleaning import UnicodeSanitizer

DEFAULT_ROWS_PER_SEGMENT = 1_000


class XlsxWorkbookConverter:
    converter_id = "xlsx_workbook"
    record_type = SPREADSHEET_RECORD_TYPE
    supported_extensions = frozenset({".xlsx"})

    def convert(self, context: ConversionContext) -> Iterator[dict[str, object]]:
        if context.source.suffix.lower() != ".xlsx":
            raise ValueError(f"Extensão XLSX não suportada: {context.source.suffix}")
        rows_per_segment = int(
            context.options.get("xlsx_rows_per_segment", DEFAULT_ROWS_PER_SEGMENT)
        )
        if rows_per_segment < 1:
            raise ValueError("A quantidade de linhas por segmento deve ser positiva")

        sanitizer = context.unicode_sanitizer or UnicodeSanitizer()
        extracted = extract_workbook(context.source, context.cancellation_token, sanitizer)
        total_workbook_rows = sum(len(dataset.rows) for dataset in extracted.datasets)
        processed = 0
        for extracted_dataset in extracted.datasets:
            total_rows = len(extracted_dataset.rows)
            chunks = (
                [
                    extracted_dataset.rows[index : index + rows_per_segment]
                    for index in range(0, total_rows, rows_per_segment)
                ]
                if extracted_dataset.rows
                else [()]
            )
            dataset_processed = 0
            for chunk in chunks:
                context.cancellation_token.raise_if_cancelled()
                row_start = dataset_processed + 1 if chunk else None
                row_end = dataset_processed + len(chunk) if chunk else None
                formulas = tuple(
                    formula
                    for logical_row, formula in extracted_dataset.formulas
                    if row_start is not None
                    and row_end is not None
                    and row_start <= logical_row <= row_end
                )
                dataset = TabularDatasetSegment(
                    name=extracted_dataset.name,
                    source_kind=extracted_dataset.source_kind,
                    reference=extracted_dataset.reference,
                    columns=extracted_dataset.columns,
                    total_rows=total_rows,
                    rows=tuple(chunk),
                    row_start=row_start,
                    row_end=row_end,
                    has_header=extracted_dataset.has_header,
                )
                yield build_spreadsheet_workbook_record(
                    source_file=context.source.name,
                    source_size_bytes=context.source_size_bytes,
                    sheet_count=extracted.sheet_count,
                    sheet=extracted_dataset.sheet,
                    dataset=dataset,
                    formulas=formulas,
                    converted_at=context.converted_at,
                    warnings=list(extracted_dataset.warnings),
                    merged_ranges=extracted_dataset.merged_ranges,
                    hidden_rows=extracted_dataset.hidden_rows,
                    hidden_columns=extracted_dataset.hidden_columns,
                )
                dataset_processed += len(chunk)
                processed += len(chunk)
                notify_progress(
                    context.progress_callback,
                    "converting",
                    processed,
                    total_workbook_rows,
                )
