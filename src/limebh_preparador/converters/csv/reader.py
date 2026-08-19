from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time
from io import StringIO
from pathlib import Path

from limebh_preparador.contracts.tabular import CsvDialect, TabularColumn, TabularValue
from limebh_preparador.converters.text.reader import read_text_source
from limebh_preparador.core.cancellation import CancellationToken
from limebh_preparador.core.cleaning import UnicodeSanitizer

SNIFF_SAMPLE_CHARS = 64 * 1024
SUPPORTED_DELIMITERS = ",;\t|"


@dataclass(frozen=True, slots=True)
class ParsedCsv:
    encoding: str
    dialect: CsvDialect
    has_header: bool
    header_inferred: bool
    columns: tuple[TabularColumn, ...]
    rows: tuple[tuple[TabularValue, ...], ...]
    warnings: tuple[str, ...]
    ragged_rows: int
    blank_rows_skipped: int
    type_inference_sample_size: int


def parse_csv_source(
    path: Path,
    cancellation_token: CancellationToken,
    sanitizer: UnicodeSanitizer,
) -> ParsedCsv:
    decoded = read_text_source(path, cancellation_token)
    if not decoded.content.strip():
        raise ValueError("O CSV está vazio")

    sample = decoded.content[:SNIFF_SAMPLE_CHARS]
    dialect, dialect_warning = _detect_dialect(sample)
    has_header, header_warning = _detect_header(sample, dialect)
    raw_rows = list(csv.reader(StringIO(decoded.content, newline=""), dialect))
    cancellation_token.raise_if_cancelled()

    blank_rows = sum(1 for row in raw_rows if not any(cell.strip() for cell in row))
    raw_rows = [row for row in raw_rows if any(cell.strip() for cell in row)]
    if not raw_rows:
        raise ValueError("O CSV não possui linhas utilizáveis")

    source_headers = raw_rows.pop(0) if has_header else []
    width = max([len(source_headers), *(len(row) for row in raw_rows)], default=0)
    if width == 0:
        raise ValueError("O CSV não possui colunas utilizáveis")
    ragged_rows = sum(1 for row in raw_rows if len(row) != width)

    padded_headers = [*source_headers, *("" for _ in range(width - len(source_headers)))]
    padded_rows = [row + [""] * (width - len(row)) for row in raw_rows]
    cleaned_headers = [sanitizer.clean(value).strip() for value in padded_headers]
    cleaned_rows = [
        [sanitizer.clean(value).strip() for value in row[:width]] for row in padded_rows
    ]
    typed_rows = [[_parse_value(value, dialect.delimiter) for value in row] for row in cleaned_rows]
    names = _normalized_column_names(cleaned_headers, width)
    columns = tuple(
        TabularColumn(
            index=index + 1,
            name=names[index],
            source_name=cleaned_headers[index] or None,
            inferred_type=_infer_column_type([row[index] for row in typed_rows]),
            nullable=any(row[index] is None for row in typed_rows),
        )
        for index in range(width)
    )
    warnings = [*decoded.warnings]
    if dialect_warning:
        warnings.append(dialect_warning)
    if header_warning:
        warnings.append(header_warning)
    if ragged_rows:
        warnings.append(f"csv_ragged_rows_normalized:{ragged_rows}")
    if blank_rows:
        warnings.append(f"csv_blank_rows_skipped:{blank_rows}")

    return ParsedCsv(
        encoding=decoded.encoding,
        dialect=CsvDialect(
            delimiter=dialect.delimiter,
            quote_character=dialect.quotechar or '"',
            escape_character=dialect.escapechar,
            line_terminator=_line_terminator(decoded.content),
        ),
        has_header=has_header,
        header_inferred=has_header,
        columns=columns,
        rows=tuple(tuple(row) for row in typed_rows),
        warnings=tuple(warnings),
        ragged_rows=ragged_rows,
        blank_rows_skipped=blank_rows,
        type_inference_sample_size=len(typed_rows),
    )


def _detect_dialect(sample: str) -> tuple[type[csv.Dialect] | csv.Dialect, str | None]:
    delimiter = max(SUPPORTED_DELIMITERS, key=lambda value: _delimiter_score(sample, value))
    if _delimiter_score(sample, delimiter)[0] == 0:
        return csv.excel, "csv_dialect_detection_failed_comma_assumed"
    try:
        return csv.Sniffer().sniff(sample, delimiters=delimiter), None
    except csv.Error:
        return _fallback_dialect(delimiter), "csv_dialect_quote_rules_defaulted"


def _delimiter_score(sample: str, delimiter: str) -> tuple[int, int, int]:
    try:
        rows = [
            row
            for row in csv.reader(StringIO(sample, newline=""), delimiter=delimiter)
            if any(cell.strip() for cell in row)
        ]
    except csv.Error:
        return (0, 0, 0)
    widths = [len(row) for row in rows if len(row) > 1]
    if not widths:
        return (0, 0, 0)
    width, frequency = Counter(widths).most_common(1)[0]
    return (frequency, width, sample.count(delimiter))


def _fallback_dialect(delimiter: str) -> type[csv.Dialect]:
    class DetectedDialect(csv.Dialect):
        doublequote = True
        escapechar = None
        lineterminator = "\r\n"
        quotechar = '"'
        quoting = csv.QUOTE_MINIMAL
        skipinitialspace = False
        strict = False

    DetectedDialect.delimiter = delimiter
    return DetectedDialect


def _detect_header(
    sample: str,
    dialect: type[csv.Dialect] | csv.Dialect,
) -> tuple[bool, str | None]:
    try:
        rows = [
            row
            for row in csv.reader(StringIO(sample, newline=""), dialect)
            if any(cell.strip() for cell in row)
        ]
    except (csv.Error, ValueError):
        return True, "csv_header_detection_failed_first_row_assumed"
    if len(rows) < 2:
        return True, "csv_header_detection_insufficient_rows_first_row_assumed"

    first = [cell.strip() for cell in rows[0]]
    if not first or not all(first):
        return False, None
    first_values = [_parse_value(value, dialect.delimiter) for value in first]
    if any(not isinstance(value, str) for value in first_values):
        return False, None

    width = len(first)
    for index in range(width):
        later_values = [
            _parse_value(row[index].strip(), dialect.delimiter)
            for row in rows[1:]
            if index < len(row) and row[index].strip()
        ]
        if any(value is not None and not isinstance(value, str) for value in later_values):
            return True, None

    normalized = [value.casefold() for value in first]
    return len(set(normalized)) == len(normalized), None


def _normalized_column_names(headers: list[str], width: int) -> list[str]:
    output: list[str] = []
    counts: dict[str, int] = {}
    for index in range(width):
        source = headers[index] if index < len(headers) else ""
        decomposed = unicodedata.normalize("NFKD", source)
        ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
        base = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_text).strip("_").lower()
        base = base or f"coluna_{index + 1}"
        counts[base] = counts.get(base, 0) + 1
        output.append(base if counts[base] == 1 else f"{base}_{counts[base]}")
    return output


def _parse_value(value: str, delimiter: str) -> TabularValue:
    if value == "":
        return None
    folded = value.casefold()
    if folded in {"true", "sim", "yes"}:
        return True
    if folded in {"false", "não", "nao", "no"}:
        return False
    if re.fullmatch(r"[-+]?(?:0|[1-9]\d*)", value):
        return int(value)
    if re.fullmatch(r"[-+]?\d+\.\d+", value):
        return float(value)
    if delimiter != "," and re.fullmatch(r"[-+]?\d+,\d+", value):
        return float(value.replace(",", "."))
    parsed_temporal = _parse_iso_temporal(value)
    return parsed_temporal if parsed_temporal is not None else value


def _parse_iso_temporal(value: str) -> date | datetime | time | None:
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return date.fromisoformat(value)
        if "T" in value or re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}.*", value):
            return datetime.fromisoformat(value)
        if re.fullmatch(r"\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?", value):
            return time.fromisoformat(value)
    except ValueError:
        return None
    return None


def _infer_column_type(values: list[TabularValue]) -> str:
    types = {_value_type(value) for value in values if value is not None}
    if not types:
        return "empty"
    if types <= {"integer", "number"}:
        return "number" if "number" in types else "integer"
    if types <= {"date", "datetime"}:
        return "datetime" if "datetime" in types else "date"
    return next(iter(types)) if len(types) == 1 else "mixed"


def _value_type(value: TabularValue) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, datetime):
        return "datetime"
    if isinstance(value, date):
        return "date"
    if isinstance(value, time):
        return "time"
    return "string"


def _line_terminator(content: str) -> str:
    if "\r\n" in content:
        return "\r\n"
    if "\r" in content:
        return "\r"
    return "\n"
