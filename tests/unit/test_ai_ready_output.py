from datetime import UTC, datetime

from preparador_dados_ia.contracts.email import build_email_record
from preparador_dados_ia.contracts.tabular import (
    CsvDialect,
    TabularColumn,
    TabularDatasetSegment,
    build_tabular_dataset_record,
)
from preparador_dados_ia.outputs.ai_ready import (
    compact_email_record,
    compact_tabular_record,
)


def test_email_output_keeps_context_without_technical_envelope() -> None:
    record = build_email_record(
        {
            "message_id": "<artificial@example.invalid>",
            "thread_id": "thread-1",
            "date": "2026-08-19T12:00:00+00:00",
            "from": [{"name": "Ana", "email": "ana@example.invalid"}],
            "to": [{"name": "Bruno", "email": "bruno@example.invalid"}],
            "cc": [],
            "bcc": [],
            "subject": "Assunto artificial",
            "body_text": "Conteúdo artificial.",
            "attachments": [
                {
                    "file_name": "anexo.pdf",
                    "media_type": "application/pdf",
                    "size_bytes": 123,
                    "content_extracted": False,
                }
            ],
        },
        source_file="caixa.mbox",
        source_size_bytes=999,
        converted_at=datetime(2026, 8, 19, tzinfo=UTC),
    )

    output = compact_email_record(record)

    assert output["subject"] == "Assunto artificial"
    assert output["body"] == "Conteúdo artificial."
    assert output["attachments"] == [{"file_name": "anexo.pdf", "media_type": "application/pdf"}]
    assert "schema_version" not in output
    assert "source" not in output
    assert "processing" not in output


def test_tabular_output_keeps_columns_and_rows_without_technical_envelope() -> None:
    dataset = TabularDatasetSegment(
        name="clientes",
        source_kind="csv",
        columns=(
            TabularColumn(1, "cliente", "Cliente", "string", False),
            TabularColumn(2, "valor", "Valor", "integer", False),
        ),
        total_rows=1,
        rows=(("Empresa Exemplo", 10),),
        row_start=1,
        row_end=1,
    )
    record = build_tabular_dataset_record(
        source_file="clientes.csv",
        source_size_bytes=100,
        encoding="utf-8",
        dialect=CsvDialect(","),
        dataset=dataset,
        converted_at=datetime(2026, 8, 19, tzinfo=UTC),
    )

    output = compact_tabular_record(record)

    assert output == {
        "source": "clientes.csv",
        "rows": {"start": 1, "end": 1, "total": 1},
        "columns": ["Cliente", "Valor"],
        "data": [["Empresa Exemplo", 10]],
    }
