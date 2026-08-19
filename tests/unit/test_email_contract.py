import json
import mailbox
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path

from jsonschema import Draft202012Validator

from preparador_dados_ia.converters.email import message_to_record

PROJECT_ROOT = Path(__file__).parents[2]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "artificial_emails.mbox"
SCHEMA = PROJECT_ROOT / "schemas" / "email_message.schema.json"
CONVERTED_AT = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)


def _records() -> list[dict[str, object]]:
    box = mailbox.mbox(FIXTURE, create=False)
    try:
        return [
            message_to_record(
                message,
                source_file=FIXTURE.name,
                source_size_bytes=FIXTURE.stat().st_size,
                include_html=False,
                converted_at=CONVERTED_AT,
            )
            for message in box
        ]
    finally:
        box.close()


def test_schema_itself_is_valid() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


def test_artificial_records_follow_email_contract() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    records = _records()

    assert len(records) == 2
    for record in records:
        validator.validate(record)
        assert record["schema_version"] == "1.0"
        assert record["record_type"] == "email_message"
        assert set(record["source"]) == {"file_name", "file_type", "size_bytes"}

    first, second = records
    assert first["data"]["thread_id"] == "1234567890001"
    assert first["data"]["gmail_labels"] == ["Caixa de entrada", "Importante"]
    assert second["data"]["in_reply_to"] == "<mensagem-1@example.invalid>"
    assert second["data"]["references"] == [
        "<inicio@example.invalid>",
        "<mensagem-1@example.invalid>",
    ]
    attachment = second["data"]["attachments"][0]
    assert attachment["file_name"] == "ata-artificial.pdf"
    assert attachment["content_extracted"] is False
    assert "body_html" not in second["data"]


def test_missing_message_id_gets_stable_generated_id() -> None:
    message = EmailMessage()
    message["From"] = "origem@example.invalid"
    message["Subject"] = "Sem ID"
    message.set_content("Conteúdo artificial")

    first = message_to_record(
        message,
        source_file="artificial.mbox",
        source_size_bytes=123,
        include_html=False,
        converted_at=CONVERTED_AT,
    )
    second = message_to_record(
        message,
        source_file="artificial.mbox",
        source_size_bytes=123,
        include_html=False,
        converted_at=CONVERTED_AT,
    )

    assert first["record_id"] == second["record_id"]
    assert first["data"]["message_id"].startswith("generated:")
    assert "message_id_generated" in first["processing"]["warnings"]
