import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator

from limebh_preparador.application.progress import ConversionProgress
from limebh_preparador.converters.base import ConversionContext
from limebh_preparador.converters.pdf import PdfDocumentConverter
from limebh_preparador.core.cancellation import CancellationToken

PROJECT_ROOT = Path(__file__).parents[2]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "artificial_document.pdf"
SCHEMA = PROJECT_ROOT / "schemas" / "pdf_document.schema.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pdf_converter_extracts_valid_contract_without_changing_source() -> None:
    source_hash = _sha256(FIXTURE)
    progress: list[ConversionProgress] = []
    context = ConversionContext(
        source=FIXTURE,
        source_size_bytes=FIXTURE.stat().st_size,
        converted_at=datetime(2026, 8, 6, 13, 0, tzinfo=UTC),
        cancellation_token=CancellationToken(),
        progress_callback=progress.append,
    )

    records = list(PdfDocumentConverter().convert(context))

    assert _sha256(FIXTURE) == source_hash
    assert len(records) == 1
    record = records[0]
    Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(record)
    assert record["source"]["file_name"] == "artificial_document.pdf"
    assert record["data"]["title"] == "Relatorio Artificial da Fase 3C"
    assert record["data"]["author"] == "LIMEBH"
    assert record["data"]["page_count"] == 3
    assert [page["extraction_method"] for page in record["data"]["pages"]] == [
        "embedded_text",
        "embedded_text",
        "none",
    ]
    assert "Procedimentos de validacao" in record["data"]["pages"][1]["text"]
    assert record["data"]["outline"][1]["children"][0]["title"] == "Controles"
    assert record["data"]["embedded_files"] == [
        {
            "file_name": "notas_artificiais.txt",
            "media_type": "text/plain",
            "size_bytes": 49,
        }
    ]
    assert record["data"]["images"] == [
        {
            "page_number": 3,
            "image_number": 1,
            "media_type": "application/octet-stream",
            "width": 1200,
            "height": 1600,
        }
    ]
    assert record["processing"]["warnings"] == ["page_0003_no_extractable_text"]
    assert record["processing"]["ocr_applied"] is False
    assert [(item.current, item.total) for item in progress] == [(1, 3), (2, 3), (3, 3)]
