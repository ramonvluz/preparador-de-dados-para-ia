import json
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator

from preparador_dados_ia.contracts.tabular import TABULAR_RECORD_TYPE
from preparador_dados_ia.converters.base import ConversionContext
from preparador_dados_ia.converters.csv import CsvDatasetConverter
from preparador_dados_ia.core.cancellation import CancellationToken
from preparador_dados_ia.core.cleaning import UnicodeSanitizer

PROJECT_ROOT = Path(__file__).parents[2]
SCHEMA = json.loads(
    (PROJECT_ROOT / "schemas" / "tabular_dataset.schema.json").read_text(encoding="utf-8")
)


def _context(source: Path, **options: object) -> ConversionContext:
    return ConversionContext(
        source=source,
        source_size_bytes=source.stat().st_size,
        converted_at=datetime(2026, 8, 19, 12, 0, tzinfo=UTC),
        cancellation_token=CancellationToken(),
        unicode_sanitizer=UnicodeSanitizer(),
        options=options,
    )


def test_csv_converter_detects_dialect_types_and_normalizes_ragged_rows(
    tmp_path: Path,
) -> None:
    source = tmp_path / "clientes.csv"
    source.write_text(
        "ID;Cliente;Receita;Ativo;Data\r\n"
        "001;Empresa Exemplo;1250,50;sim;2026-08-01\r\n"
        "2;Instituto Exemplo;;não;2026-08-02\r\n"
        "\r\n"
        "3;Órgão\u200b Público;980,00;true\r\n",
        encoding="utf-8",
        newline="",
    )

    records = list(CsvDatasetConverter().convert(_context(source)))

    assert len(records) == 1
    record = records[0]
    Draft202012Validator(SCHEMA).validate(record)
    assert record["record_type"] == TABULAR_RECORD_TYPE
    assert record["data"]["dialect"]["delimiter"] == ";"
    assert [column["name"] for column in record["data"]["dataset"]["columns"]] == [
        "id",
        "cliente",
        "receita",
        "ativo",
        "data",
    ]
    rows = record["data"]["dataset"]["rows"]
    assert rows[0] == ["001", "Empresa Exemplo", 1250.5, True, "2026-08-01"]
    assert rows[2] == ["3", "Órgão Público", 980.0, True, None]
    assert record["data"]["dataset"]["columns"][0]["inferred_type"] == "string"
    assert record["processing"]["ragged_rows"] == 1
    assert record["processing"]["blank_rows_skipped"] == 1


def test_csv_converter_segments_rows_without_losing_ranges(tmp_path: Path) -> None:
    source = tmp_path / "dados.csv"
    source.write_text("Código,Valor\n1,10\n2,20\n3,30\n", encoding="utf-8")

    records = list(CsvDatasetConverter().convert(_context(source, csv_rows_per_segment=2)))

    assert len(records) == 2
    datasets = [record["data"]["dataset"] for record in records]
    assert [(item["row_start"], item["row_end"]) for item in datasets] == [(1, 2), (3, 3)]
    assert all(item["total_rows"] == 3 for item in datasets)


def test_csv_without_header_generates_stable_column_names(tmp_path: Path) -> None:
    source = tmp_path / "sem_cabecalho.csv"
    source.write_text("1;10\n2;20\n3;30\n", encoding="utf-8")

    record = next(CsvDatasetConverter().convert(_context(source)))

    dataset = record["data"]["dataset"]
    assert dataset["has_header"] is False
    assert [column["name"] for column in dataset["columns"]] == ["coluna_1", "coluna_2"]
    assert dataset["rows"][0] == [1, 10]


def test_csv_mixed_text_column_preserves_numeric_and_boolean_looking_values(
    tmp_path: Path,
) -> None:
    source = tmp_path / "titulos.csv"
    source.write_text(
        "Título,Ano\nFilme A,2024\n1922,1922\n46,2020\nNo,2021\n",
        encoding="utf-8",
    )

    record = next(CsvDatasetConverter().convert(_context(source)))

    dataset = record["data"]["dataset"]
    assert dataset["columns"][0]["inferred_type"] == "string"
    assert dataset["columns"][1]["inferred_type"] == "integer"
    assert [row[0] for row in dataset["rows"]] == ["Filme A", "1922", "46", "No"]
    assert [row[1] for row in dataset["rows"]] == [2024, 1922, 2020, 2021]
