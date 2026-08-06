import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator

from limebh_preparador.application.progress import ConversionProgress
from limebh_preparador.converters.base import ConversionContext
from limebh_preparador.converters.word import WordDocumentConverter
from limebh_preparador.core.cancellation import CancellationToken

PROJECT_ROOT = Path(__file__).parents[2]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "artificial_document.docx"
SCHEMA = PROJECT_ROOT / "schemas" / "word_document.schema.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_word_converter_extracts_ordered_valid_contract_without_changing_source() -> None:
    source_hash = _sha256(FIXTURE)
    progress: list[ConversionProgress] = []
    context = ConversionContext(
        source=FIXTURE,
        source_size_bytes=FIXTURE.stat().st_size,
        converted_at=datetime(2026, 8, 6, 15, 30, tzinfo=UTC),
        cancellation_token=CancellationToken(),
        progress_callback=progress.append,
    )

    records = list(WordDocumentConverter().convert(context))

    assert _sha256(FIXTURE) == source_hash
    assert len(records) == 1
    record = records[0]
    Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(record)
    assert record["source"]["file_name"] == "artificial_document.docx"
    assert record["data"]["title"] == "Guia Artificial de Validação 3D"
    assert record["data"]["author"] == "LIMEBH"
    assert len(record["data"]["blocks"]) == 18
    assert [block["type"] for block in record["data"]["blocks"]][3:7] == [
        "heading",
        "paragraph",
        "heading",
        "list_item",
    ]
    list_items = [block for block in record["data"]["blocks"] if block["type"] == "list_item"]
    assert [(item["level"], item["ordered"]) for item in list_items] == [
        (0, False),
        (0, False),
        (1, False),
        (0, True),
        (0, True),
    ]
    table = next(block for block in record["data"]["blocks"] if block["type"] == "table")
    assert table["has_header"] is True
    assert table["rows"][3][2] == "Risco | mitigação"
    assert len(record["data"]["sections"]) == 5
    assert record["data"]["sections"][1] == {
        "title": "1.1 Critérios",
        "level": 2,
        "start_block": 5,
        "end_block": 10,
    }
    assert record["processing"]["images_omitted"] == 1
    assert record["processing"]["headers_footers_omitted"] is True
    assert record["processing"]["features_omitted"] == []
    assert progress[0].current == 1
    assert progress[-1].current == progress[-1].total
