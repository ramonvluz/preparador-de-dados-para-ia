from __future__ import annotations

from collections.abc import Iterator

from limebh_preparador.application.progress import notify_progress
from limebh_preparador.contracts.tabular import (
    TABULAR_RECORD_TYPE,
    TabularDatasetSegment,
    build_tabular_dataset_record,
)
from limebh_preparador.converters.base import ConversionContext
from limebh_preparador.converters.csv.reader import parse_csv_source
from limebh_preparador.core.cleaning import UnicodeSanitizer

DEFAULT_ROWS_PER_SEGMENT = 1_000


class CsvDatasetConverter:
    converter_id = "csv_dataset"
    record_type = TABULAR_RECORD_TYPE
    supported_extensions = frozenset({".csv"})

    def convert(self, context: ConversionContext) -> Iterator[dict[str, object]]:
        if context.source.suffix.lower() != ".csv":
            raise ValueError(f"Extensão CSV não suportada: {context.source.suffix}")
        rows_per_segment = int(
            context.options.get("csv_rows_per_segment", DEFAULT_ROWS_PER_SEGMENT)
        )
        if rows_per_segment < 1:
            raise ValueError("A quantidade de linhas por segmento deve ser positiva")

        sanitizer = context.unicode_sanitizer or UnicodeSanitizer()
        parsed = parse_csv_source(context.source, context.cancellation_token, sanitizer)
        total_rows = len(parsed.rows)
        chunks = (
            [
                parsed.rows[index : index + rows_per_segment]
                for index in range(0, total_rows, rows_per_segment)
            ]
            if parsed.rows
            else [()]
        )
        processed = 0
        for chunk in chunks:
            context.cancellation_token.raise_if_cancelled()
            row_start = processed + 1 if chunk else None
            row_end = processed + len(chunk) if chunk else None
            dataset = TabularDatasetSegment(
                name=context.source.stem,
                source_kind="csv",
                columns=parsed.columns,
                total_rows=total_rows,
                rows=tuple(chunk),
                row_start=row_start,
                row_end=row_end,
                has_header=parsed.has_header,
            )
            yield build_tabular_dataset_record(
                source_file=context.source.name,
                source_size_bytes=context.source_size_bytes,
                encoding=parsed.encoding,
                dialect=parsed.dialect,
                dataset=dataset,
                converted_at=context.converted_at,
                warnings=list(parsed.warnings),
                header_inferred=parsed.header_inferred,
                ragged_rows=parsed.ragged_rows,
                blank_rows_skipped=parsed.blank_rows_skipped,
                type_inference_sample_size=parsed.type_inference_sample_size,
            )
            processed += len(chunk)
            notify_progress(context.progress_callback, "converting", processed, total_rows)
