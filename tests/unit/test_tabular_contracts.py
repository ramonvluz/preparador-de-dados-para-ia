import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from preparador_dados_ia.contracts.tabular import (
    CsvDialect,
    SpreadsheetFormula,
    SpreadsheetSheet,
    TabularColumn,
    TabularDatasetSegment,
    build_spreadsheet_workbook_record,
    build_tabular_dataset_record,
)

PROJECT_ROOT = Path(__file__).parents[2]
SCHEMA_DIR = PROJECT_ROOT / "schemas"
CONVERTED_AT = datetime(2026, 8, 6, 12, 0, tzinfo=UTC)


def _schema(name: str) -> dict[str, object]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "schema_name",
    ["tabular_dataset.schema.json", "spreadsheet_workbook.schema.json"],
)
def test_tabular_schemas_are_valid_draft_2020_12(schema_name: str) -> None:
    Draft202012Validator.check_schema(_schema(schema_name))


def test_csv_record_is_typed_schema_valid_and_stable() -> None:
    dataset = TabularDatasetSegment(
        name="clientes",
        source_kind="csv",
        columns=(
            TabularColumn(1, "id", "ID", "integer", False),
            TabularColumn(2, "cliente", "Cliente", "string", False),
            TabularColumn(3, "receita", "Receita", "number", True),
            TabularColumn(4, "ativo", "Ativo", "boolean", False),
            TabularColumn(5, "data", "Data", "date", False),
        ),
        total_rows=2,
        rows=(
            (1, "Empresa Exemplo", 1250.5, True, date(2026, 8, 1)),
            (2, "Instituto Exemplo", None, False, date(2026, 8, 2)),
        ),
        row_start=1,
        row_end=2,
    )
    kwargs = {
        "source_file": "clientes.csv",
        "source_size_bytes": 321,
        "encoding": "utf-8",
        "dialect": CsvDialect(delimiter=";"),
        "dataset": dataset,
        "converted_at": CONVERTED_AT,
        "type_inference_sample_size": 2,
    }

    record = build_tabular_dataset_record(**kwargs)
    repeated = build_tabular_dataset_record(**kwargs)
    Draft202012Validator(_schema("tabular_dataset.schema.json")).validate(record)

    assert record["record_id"] == repeated["record_id"]
    assert record["data"]["dataset"]["rows"][0][4] == "2026-08-01"
    assert record["data"]["dialect"]["delimiter"] == ";"


def test_xlsx_record_keeps_sheet_range_and_formula_metadata() -> None:
    dataset = TabularDatasetSegment(
        name="Vendas",
        source_kind="excel_table",
        reference="A1:D3",
        columns=(
            TabularColumn(1, "produto", "Produto", "string", False),
            TabularColumn(2, "quantidade", "Quantidade", "integer", False),
            TabularColumn(3, "preco", "Preço", "number", False),
            TabularColumn(4, "total", "Total", "number", False),
        ),
        total_rows=2,
        rows=(("Serviço A", 2, 100.0, 200.0), ("Serviço B", 1, 75.0, 75.0)),
        row_start=1,
        row_end=2,
    )
    record = build_spreadsheet_workbook_record(
        source_file="vendas.xlsx",
        source_size_bytes=2048,
        sheet_count=2,
        sheet=SpreadsheetSheet(index=1, name="Vendas", used_range="A1:D3"),
        dataset=dataset,
        formulas=(
            SpreadsheetFormula("D2", "=B2*C2", 200.0),
            SpreadsheetFormula("D3", "=B3*C3", 75.0),
        ),
        converted_at=CONVERTED_AT,
    )
    Draft202012Validator(_schema("spreadsheet_workbook.schema.json")).validate(record)

    assert record["data"]["sheet"]["name"] == "Vendas"
    assert record["data"]["dataset"]["reference"] == "A1:D3"
    assert record["processing"]["formula_policy"] == "cached_value_with_formula_metadata"
    assert record["processing"]["external_links_followed"] is False


@pytest.mark.parametrize(
    ("columns", "rows", "message"),
    [
        (
            (
                TabularColumn(1, "codigo", "Código", "integer", False),
                TabularColumn(2, "CODIGO", "Código repetido", "integer", False),
            ),
            ((1, 2),),
            "únicos",
        ),
        (
            (TabularColumn(1, "codigo", "Código", "integer", False),),
            ((1, 2),),
            "mesma largura",
        ),
        (
            (TabularColumn(1, "valor", "Valor", "number", False),),
            ((float("inf"),),),
            "finitos",
        ),
    ],
)
def test_dataset_rejects_ambiguous_or_invalid_rows(columns, rows, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        TabularDatasetSegment(
            name="dados",
            source_kind="csv",
            columns=columns,
            total_rows=1,
            rows=rows,
            row_start=1,
            row_end=1,
        )


def test_formula_requires_explicit_formula_marker() -> None:
    with pytest.raises(ValueError, match="começar"):
        SpreadsheetFormula("D2", "B2*C2", 200.0)
