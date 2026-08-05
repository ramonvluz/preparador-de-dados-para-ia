import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from limebh_preparador.application.conversion import (
    ConversionSettings,
    DestinationProfile,
    convert_mbox,
)
from limebh_preparador.application.progress import ConversionProgress
from limebh_preparador.core.cancellation import CancellationToken

PROJECT_ROOT = Path(__file__).parents[2]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "artificial_emails.mbox"
SCHEMA = PROJECT_ROOT / "schemas" / "email_message.schema.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_platform_conversion_preserves_source_and_generates_contract_outputs(
    tmp_path: Path,
) -> None:
    source_hash = _sha256(FIXTURE)
    output = tmp_path / "resultado"
    report = convert_mbox(
        FIXTURE,
        output,
        settings=ConversionSettings(max_size_mb=0.01, max_tokens=5_000),
    )

    assert _sha256(FIXTURE) == source_hash
    assert report["result"] == "success"
    assert report["converted_messages"] == 2
    assert report["failed_messages"] == 0
    assert report["attachments_catalogued"] == 1
    assert (output / "LEIA-ME.txt").is_file()
    assert (output / "relatorio_conversao.json").is_file()

    validator = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    records: list[dict[str, object]] = []
    ready_text = ""
    for part in report["parts"]:
        path = output / "PRONTO_PARA_IA" / part["file"]
        part_text = path.read_text(encoding="utf-8")
        ready_text += part_text
        part_records = json.loads(part_text)
        records.extend(part_records)
        assert path.stat().st_size <= report["settings"]["max_bytes"]
    assert len(records) == 2
    assert "Y29udGV1ZG8gYXJ0aWZpY2lhbA==" not in ready_text
    for record in records:
        validator.validate(record)
        assert "absolute_path" not in record["source"]
        assert record["source"]["file_name"] == FIXTURE.name

    with pytest.raises(FileExistsError):
        convert_mbox(FIXTURE, output)


def test_api_profile_generates_partitioned_jsonl(tmp_path: Path) -> None:
    output = tmp_path / "api"
    report = convert_mbox(
        FIXTURE,
        output,
        settings=ConversionSettings(profile=DestinationProfile.API),
    )

    assert report["output_format"] == "jsonl"
    assert report["parts"]
    for part in report["parts"]:
        assert part["file"].endswith(".jsonl")
        lines = (output / "PRONTO_PARA_IA" / part["file"]).read_text(encoding="utf-8").splitlines()
        assert all(json.loads(line)["record_type"] == "email_message" for line in lines)


def test_cancellation_keeps_only_complete_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "cancelado"
    token = CancellationToken()

    def cancel_after_first(progress: ConversionProgress) -> None:
        if progress.stage == "converting" and progress.current == 1:
            token.cancel()

    report = convert_mbox(
        FIXTURE,
        output,
        cancellation_token=token,
        progress_callback=cancel_after_first,
    )

    assert report["result"] == "cancelled"
    assert report["converted_messages"] == 1
    assert list(output.rglob("*.tmp")) == []
    assert (output / "relatorio_conversao.json").is_file()
    assert (output / "PRONTO_PARA_IA" / report["parts"][0]["file"]).is_file()
