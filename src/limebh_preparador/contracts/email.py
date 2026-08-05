from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from limebh_preparador.contracts.common import SCHEMA_VERSION

RECORD_TYPE = "email_message"


def _generated_message_id(data: dict[str, object]) -> str:
    sender = data.get("from")
    fingerprint = "|".join(
        [
            str(data.get("date_raw") or ""),
            str(sender or ""),
            str(data.get("subject") or ""),
            str(data.get("body_text") or "")[:1000],
        ]
    )
    digest = hashlib.sha256(fingerprint.encode("utf-8", errors="replace")).hexdigest()
    return f"generated:{digest}"


def build_email_record(
    data: dict[str, object],
    *,
    source_file: str,
    source_size_bytes: int,
    converted_at: datetime | None = None,
    warnings: list[str] | None = None,
) -> dict[str, object]:
    """Aplica o envelope comum sem incluir o caminho absoluto da fonte."""

    record_data = dict(data)
    record_warnings = list(warnings or [])
    raw_id = record_data.get("message_id")
    if not isinstance(raw_id, str) or not raw_id:
        raw_id = _generated_message_id(record_data)
        record_data["message_id"] = raw_id
        record_warnings.append("message_id_generated")

    timestamp = converted_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)

    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": RECORD_TYPE,
        "record_id": "email_"
        + hashlib.sha256(raw_id.encode("utf-8", errors="replace")).hexdigest()[:24],
        "source": {
            "file_name": source_file,
            "file_type": "mbox",
            "size_bytes": source_size_bytes,
        },
        "data": record_data,
        "processing": {
            "converted_at": timestamp.isoformat(),
            "unicode_cleaned": True,
            "warnings": record_warnings,
        },
    }
