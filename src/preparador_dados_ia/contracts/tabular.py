from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import TypeAlias

from preparador_dados_ia.contracts.common import build_document_record

TABULAR_RECORD_TYPE = "tabular_dataset"
SPREADSHEET_RECORD_TYPE = "spreadsheet_workbook"
TabularValue: TypeAlias = str | int | float | bool | date | datetime | time | None

INFERRED_TYPES = frozenset(
    {"empty", "boolean", "integer", "number", "date", "datetime", "time", "string", "mixed"}
)
SOURCE_KINDS = frozenset({"csv", "worksheet_range", "excel_table"})
SHEET_VISIBILITIES = frozenset({"visible", "hidden", "very_hidden"})


@dataclass(frozen=True, slots=True)
class TabularColumn:
    index: int
    name: str
    source_name: str | None
    inferred_type: str
    nullable: bool

    def __post_init__(self) -> None:
        if self.index < 1:
            raise ValueError("O índice da coluna deve começar em 1")
        if not self.name.strip():
            raise ValueError("O nome normalizado da coluna é obrigatório")
        if self.inferred_type not in INFERRED_TYPES:
            raise ValueError(f"Tipo tabular inferido inválido: {self.inferred_type}")

    def as_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "name": self.name,
            "source_name": self.source_name,
            "inferred_type": self.inferred_type,
            "nullable": self.nullable,
        }


@dataclass(frozen=True, slots=True)
class TabularDatasetSegment:
    name: str
    source_kind: str
    columns: tuple[TabularColumn, ...]
    total_rows: int
    rows: tuple[tuple[TabularValue, ...], ...]
    row_start: int | None
    row_end: int | None
    has_header: bool = True
    reference: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("O nome do conjunto tabular é obrigatório")
        if self.source_kind not in SOURCE_KINDS:
            raise ValueError(f"Origem tabular inválida: {self.source_kind}")
        if not self.columns:
            raise ValueError("O conjunto tabular deve possuir ao menos uma coluna")
        if self.total_rows < 0:
            raise ValueError("A quantidade total de linhas não pode ser negativa")
        if [column.index for column in self.columns] != list(range(1, len(self.columns) + 1)):
            raise ValueError("Os índices das colunas devem ser consecutivos e começar em 1")
        names = [column.name.casefold() for column in self.columns]
        if len(set(names)) != len(names):
            raise ValueError("Os nomes normalizados das colunas devem ser únicos")
        if self.source_kind == "csv" and self.reference is not None:
            raise ValueError("Um CSV não deve declarar intervalo de planilha")
        if self.source_kind != "csv" and not self.reference:
            raise ValueError("Intervalos XLSX devem declarar uma referência de células")
        self._validate_rows()

    def _validate_rows(self) -> None:
        if not self.rows:
            if self.row_start is not None or self.row_end is not None:
                raise ValueError("Um segmento vazio não deve declarar intervalo de linhas")
            return
        if self.row_start is None or self.row_end is None or self.row_start < 1:
            raise ValueError("Um segmento com dados deve declarar linhas inicial e final")
        if self.row_end != self.row_start + len(self.rows) - 1:
            raise ValueError("O intervalo não corresponde à quantidade de linhas do segmento")
        if self.row_end > self.total_rows:
            raise ValueError("O segmento ultrapassa a quantidade total de linhas")
        width = len(self.columns)
        for row in self.rows:
            if len(row) != width:
                raise ValueError("Todas as linhas devem possuir a mesma largura das colunas")
            for value in row:
                _normalize_value(value)

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "source_kind": self.source_kind,
            "reference": self.reference,
            "has_header": self.has_header,
            "columns": [column.as_dict() for column in self.columns],
            "total_rows": self.total_rows,
            "row_start": self.row_start,
            "row_end": self.row_end,
            "rows": [[_normalize_value(value) for value in row] for row in self.rows],
        }


@dataclass(frozen=True, slots=True)
class CsvDialect:
    delimiter: str
    quote_character: str = '"'
    escape_character: str | None = None
    line_terminator: str = "\r\n"

    def __post_init__(self) -> None:
        _validate_character(self.delimiter, "delimitador")
        _validate_character(self.quote_character, "caractere de aspas")
        if self.escape_character is not None:
            _validate_character(self.escape_character, "caractere de escape")
        if not self.line_terminator:
            raise ValueError("O terminador de linha é obrigatório")

    def as_dict(self) -> dict[str, object]:
        return {
            "delimiter": self.delimiter,
            "quote_character": self.quote_character,
            "escape_character": self.escape_character,
            "line_terminator": self.line_terminator,
        }


@dataclass(frozen=True, slots=True)
class SpreadsheetSheet:
    index: int
    name: str
    visibility: str = "visible"
    used_range: str | None = None

    def __post_init__(self) -> None:
        if self.index < 1:
            raise ValueError("O índice da aba deve começar em 1")
        if not self.name.strip():
            raise ValueError("O nome da aba é obrigatório")
        if self.visibility not in SHEET_VISIBILITIES:
            raise ValueError(f"Visibilidade de aba inválida: {self.visibility}")

    def as_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "name": self.name,
            "visibility": self.visibility,
            "used_range": self.used_range,
        }


@dataclass(frozen=True, slots=True)
class SpreadsheetFormula:
    cell_reference: str
    formula: str
    cached_value: TabularValue = None

    def __post_init__(self) -> None:
        if not self.cell_reference.strip():
            raise ValueError("A referência da fórmula é obrigatória")
        if not self.formula.startswith("="):
            raise ValueError("A fórmula deve começar com '='")
        _normalize_value(self.cached_value)

    def as_dict(self) -> dict[str, object]:
        return {
            "cell_reference": self.cell_reference,
            "formula": self.formula,
            "cached_value": _normalize_value(self.cached_value),
        }


def build_tabular_dataset_record(
    *,
    source_file: str,
    source_size_bytes: int,
    encoding: str,
    dialect: CsvDialect,
    dataset: TabularDatasetSegment,
    converted_at: datetime | None = None,
    warnings: list[str] | None = None,
    unicode_cleaned: bool = True,
    header_inferred: bool = False,
    ragged_rows: int = 0,
    blank_rows_skipped: int = 0,
    type_inference_sample_size: int = 0,
) -> dict[str, object]:
    if dataset.source_kind != "csv":
        raise ValueError("O contrato CSV exige um conjunto com origem 'csv'")
    if not encoding.strip():
        raise ValueError("A codificação do CSV é obrigatória")
    _validate_metrics(ragged_rows, blank_rows_skipped, type_inference_sample_size)
    return build_document_record(
        record_type=TABULAR_RECORD_TYPE,
        record_prefix="tabular",
        source_file=source_file,
        source_file_type="csv",
        source_size_bytes=source_size_bytes,
        logical_key=_dataset_key(dataset),
        data={"encoding": encoding, "dialect": dialect.as_dict(), "dataset": dataset.as_dict()},
        converted_at=converted_at,
        warnings=warnings,
        unicode_cleaned=unicode_cleaned,
        processing={
            "header_inferred": header_inferred,
            "ragged_rows": ragged_rows,
            "blank_rows_skipped": blank_rows_skipped,
            "type_inference_sample_size": type_inference_sample_size,
        },
    )


def build_spreadsheet_workbook_record(
    *,
    source_file: str,
    source_size_bytes: int,
    sheet_count: int,
    sheet: SpreadsheetSheet,
    dataset: TabularDatasetSegment,
    formulas: Sequence[SpreadsheetFormula] = (),
    converted_at: datetime | None = None,
    warnings: list[str] | None = None,
    unicode_cleaned: bool = True,
    merged_ranges: int = 0,
    hidden_rows: int = 0,
    hidden_columns: int = 0,
) -> dict[str, object]:
    if sheet_count < 1 or sheet.index > sheet_count:
        raise ValueError("A quantidade de abas deve incluir o índice da aba atual")
    if dataset.source_kind not in {"worksheet_range", "excel_table"}:
        raise ValueError("O contrato XLSX exige um intervalo ou tabela de planilha")
    _validate_metrics(merged_ranges, hidden_rows, hidden_columns)
    formula_refs = [formula.cell_reference.casefold() for formula in formulas]
    if len(set(formula_refs)) != len(formula_refs):
        raise ValueError("As referências de fórmula devem ser únicas")
    return build_document_record(
        record_type=SPREADSHEET_RECORD_TYPE,
        record_prefix="spreadsheet",
        source_file=source_file,
        source_file_type="xlsx",
        source_size_bytes=source_size_bytes,
        logical_key=f"{sheet.index}:{sheet.name}:{_dataset_key(dataset)}",
        data={
            "workbook": {"sheet_count": sheet_count},
            "sheet": sheet.as_dict(),
            "dataset": dataset.as_dict(),
            "formulas": [formula.as_dict() for formula in formulas],
        },
        converted_at=converted_at,
        warnings=warnings,
        unicode_cleaned=unicode_cleaned,
        processing={
            "formula_policy": "cached_value_with_formula_metadata",
            "formula_cells": len(formulas),
            "merged_ranges": merged_ranges,
            "hidden_rows": hidden_rows,
            "hidden_columns": hidden_columns,
            "external_links_followed": False,
        },
    )


def _dataset_key(dataset: TabularDatasetSegment) -> str:
    rows = (
        f"{dataset.row_start}-{dataset.row_end}"
        if dataset.row_start is not None and dataset.row_end is not None
        else "empty"
    )
    return f"{dataset.source_kind}:{dataset.name}:{dataset.reference or '-'}:{rows}"


def _normalize_value(value: TabularValue) -> str | int | float | bool | None:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Valores numéricos tabulares devem ser finitos")
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    raise TypeError(f"Tipo de célula não suportado: {type(value).__name__}")


def _validate_character(value: str, label: str) -> None:
    if len(value) != 1:
        raise ValueError(f"O {label} deve conter exatamente um caractere")


def _validate_metrics(*values: int) -> None:
    if any(value < 0 for value in values):
        raise ValueError("Métricas tabulares não podem ser negativas")
