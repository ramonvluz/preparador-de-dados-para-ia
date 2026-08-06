import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator

from limebh_preparador.converters.base import ConversionContext
from limebh_preparador.converters.text import TextDocumentConverter
from limebh_preparador.core.cancellation import CancellationToken

PROJECT_ROOT = Path(__file__).parents[2]
SCHEMA = PROJECT_ROOT / "schemas" / "text_document.schema.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_text_converter_builds_valid_contract_without_changing_source(tmp_path: Path) -> None:
    source = tmp_path / "manual.md"
    source.write_text("# Manual\n\n## Uso\n\nConteúdo local.\n", encoding="utf-8")
    source_hash = _sha256(source)
    context = ConversionContext(
        source=source,
        source_size_bytes=source.stat().st_size,
        converted_at=datetime(2026, 8, 6, 9, 0, tzinfo=UTC),
        cancellation_token=CancellationToken(),
    )

    records = list(TextDocumentConverter().convert(context))

    assert _sha256(source) == source_hash
    assert len(records) == 1
    record = records[0]
    Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(record)
    assert record["source"]["file_name"] == "manual.md"
    assert record["source"]["file_type"] == "markdown"
    assert record["data"]["encoding"] == "utf-8"
    assert [heading["text"] for heading in record["data"]["headings"]] == ["Manual", "Uso"]
