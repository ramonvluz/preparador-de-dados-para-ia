from __future__ import annotations

from datetime import datetime
from email.message import Message

from limebh_preparador.contracts.email import build_email_record
from limebh_preparador.converters.email.parser import extract_email_data


def message_to_record(
    message: Message,
    *,
    source_file: str,
    source_size_bytes: int,
    include_html: bool,
    converted_at: datetime,
) -> dict[str, object]:
    data, warnings = extract_email_data(message, include_html=include_html)
    return build_email_record(
        data,
        source_file=source_file,
        source_size_bytes=source_size_bytes,
        converted_at=converted_at,
        warnings=warnings,
    )
