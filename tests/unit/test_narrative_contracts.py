import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from limebh_preparador.contracts.pdf import (
    PdfEmbeddedFile,
    PdfImage,
    PdfOutlineItem,
    PdfPage,
    build_pdf_document_record,
)
from limebh_preparador.contracts.text import (
    TextHeading,
    TextSection,
    build_text_document_record,
)
from limebh_preparador.contracts.word import (
    WordHeading,
    WordListItem,
    WordParagraph,
    WordSection,
    WordTable,
    build_word_document_record,
)

PROJECT_ROOT = Path(__file__).parents[2]
SCHEMA_DIR = PROJECT_ROOT / "schemas"
CONVERTED_AT = datetime(2026, 8, 5, 16, 30, tzinfo=UTC)


def _schema(name: str) -> dict[str, object]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "schema_name",
    [
        "text_document.schema.json",
        "pdf_document.schema.json",
        "word_document.schema.json",
    ],
)
def test_narrative_schemas_are_valid_draft_2020_12(schema_name: str) -> None:
    Draft202012Validator.check_schema(_schema(schema_name))


def test_text_document_record_follows_contract_and_has_stable_id() -> None:
    kwargs = {
        "source_file": "orientacoes.md",
        "source_file_type": "markdown",
        "source_size_bytes": 142,
        "encoding": "utf-8",
        "content": "# Atendimento\n\nProcedimento local.",
        "title": "Atendimento",
        "headings": [TextHeading(level=1, text="Atendimento", line_number=1)],
        "sections": [
            TextSection(
                title="Atendimento",
                level=1,
                content="Procedimento local.",
                start_line=1,
                end_line=3,
            )
        ],
        "converted_at": CONVERTED_AT,
    }

    record = build_text_document_record(**kwargs)
    repeated = build_text_document_record(**kwargs)
    Draft202012Validator(_schema("text_document.schema.json")).validate(record)

    assert record["record_id"] == repeated["record_id"]
    assert record["record_type"] == "text_document"
    assert record["source"] == {
        "file_name": "orientacoes.md",
        "file_type": "markdown",
        "size_bytes": 142,
    }
    assert record["data"]["content_format"] == "markdown"


def test_pdf_document_record_preserves_page_references_and_catalogs() -> None:
    record = build_pdf_document_record(
        source_file="relatorio.pdf",
        source_size_bytes=2048,
        title="Relatório",
        author="LIMEBH",
        pages=[
            PdfPage(page_number=1, text="Página textual", extraction_method="embedded_text"),
            PdfPage(page_number=2, text="Página digitalizada", extraction_method="ocr"),
        ],
        outline=[PdfOutlineItem(title="Introdução", page_number=1)],
        embedded_files=[
            PdfEmbeddedFile(
                file_name="dados.csv",
                media_type="text/csv",
                size_bytes=321,
            )
        ],
        images=[
            PdfImage(
                page_number=2,
                image_number=1,
                media_type="image/png",
                width=800,
                height=600,
            )
        ],
        converted_at=CONVERTED_AT,
    )
    Draft202012Validator(_schema("pdf_document.schema.json")).validate(record)

    assert record["data"]["page_count"] == 2
    assert record["data"]["pages"][1]["page_number"] == 2
    assert record["processing"]["ocr_applied"] is True


def test_word_document_record_preserves_ordered_blocks_and_sections() -> None:
    blocks = [
        WordHeading(text="Contratação", level=1),
        WordParagraph(text="Orientações gerais.", style="Normal"),
        WordListItem(text="Conferir documentos", level=0, ordered=False),
        WordTable(
            rows=(("Item", "Responsável"), ("Cadastro", "Equipe")),
            has_header=True,
        ),
    ]
    record = build_word_document_record(
        source_file="manual.docx",
        source_size_bytes=4096,
        title="Manual",
        author="LIMEBH",
        blocks=blocks,
        sections=[WordSection(title="Contratação", level=1, start_block=0, end_block=3)],
        converted_at=CONVERTED_AT,
    )
    Draft202012Validator(_schema("word_document.schema.json")).validate(record)

    assert [block["type"] for block in record["data"]["blocks"]] == [
        "heading",
        "paragraph",
        "list_item",
        "table",
    ]
    assert record["data"]["sections"][0]["end_block"] == 3


def test_document_envelope_rejects_absolute_or_relative_paths() -> None:
    with pytest.raises(ValueError, match="somente o nome"):
        build_text_document_record(
            source_file=r"C:\documentos\interno.txt",
            source_file_type="txt",
            source_size_bytes=1,
            encoding="utf-8",
            content="teste",
            converted_at=CONVERTED_AT,
        )
