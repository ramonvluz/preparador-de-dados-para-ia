from __future__ import annotations

import csv
import re
from collections.abc import Iterable
from datetime import UTC
from email.header import decode_header, make_header
from email.message import Message
from email.utils import getaddresses, parsedate_to_datetime

from preparador_dados_ia.core.cleaning import html_to_text


def decode_header_value(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return str(make_header(decode_header(value))).strip()
    except Exception:
        return str(value).strip()


def decode_payload(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        raw = part.get_payload()
        return raw if isinstance(raw, str) else ""
    for charset in (part.get_content_charset(), "utf-8", "windows-1252", "latin-1"):
        if charset:
            try:
                return payload.decode(charset)
            except (LookupError, UnicodeDecodeError):
                pass
    return payload.decode("utf-8", errors="replace")


def parse_addresses(message: Message, header_name: str) -> list[dict[str, str]]:
    decoded = [decode_header_value(value) or "" for value in message.get_all(header_name, [])]
    return [
        {"name": decode_header_value(name) or "", "email": address}
        for name, address in getaddresses(decoded)
        if name or address
    ]


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def message_bodies(message: Message) -> tuple[str, str | None, list[dict[str, object]]]:
    plain_parts: list[str] = []
    html_parts: list[str] = []
    attachments: list[dict[str, object]] = []
    parts: Iterable[Message] = message.walk() if message.is_multipart() else [message]

    for part in parts:
        if part.is_multipart():
            continue
        media_type = part.get_content_type().lower()
        filename = decode_header_value(part.get_filename())
        raw_payload = part.get_payload(decode=True)
        disposition = (part.get_content_disposition() or "").lower()
        if disposition == "attachment" or filename:
            attachments.append(
                {
                    "file_name": filename,
                    "media_type": media_type,
                    "size_bytes": len(raw_payload) if raw_payload is not None else None,
                    "content_extracted": False,
                }
            )
        elif media_type == "text/plain":
            if text := decode_payload(part).strip():
                plain_parts.append(text)
        elif media_type == "text/html":
            if text := decode_payload(part).strip():
                html_parts.append(text)

    body_html = "\n\n".join(html_parts) or None
    body_text = "\n\n".join(plain_parts)
    if not body_text and body_html:
        body_text = html_to_text(body_html)
    return body_text, body_html, attachments


def parse_gmail_labels(message: Message) -> list[str]:
    labels: list[str] = []
    for raw in message.get_all("X-Gmail-Labels", []):
        value = decode_header_value(raw) or ""
        try:
            labels.extend(item.strip() for item in next(csv.reader([value])) if item.strip())
        except (csv.Error, StopIteration):
            labels.extend(item.strip() for item in value.split(",") if item.strip())
    return labels


def parse_references(message: Message) -> list[str]:
    references: list[str] = []
    for raw in message.get_all("References", []):
        value = decode_header_value(raw) or ""
        references.extend(re.findall(r"<[^>]+>", value) or value.split())
    return references


def extract_email_data(
    message: Message,
    *,
    include_html: bool,
) -> tuple[dict[str, object], list[str]]:
    body_text, body_html, attachments = message_bodies(message)
    date_raw = decode_header_value(message.get("Date"))
    parsed_date = parse_date(message.get("Date"))
    warnings: list[str] = []
    if date_raw and parsed_date is None:
        warnings.append("date_unparseable")

    data: dict[str, object] = {
        "message_id": decode_header_value(message.get("Message-ID")),
        "thread_id": decode_header_value(message.get("X-GM-THRID")),
        "gmail_labels": parse_gmail_labels(message),
        "date": parsed_date,
        "date_raw": date_raw,
        "from": parse_addresses(message, "From"),
        "to": parse_addresses(message, "To"),
        "cc": parse_addresses(message, "Cc"),
        "bcc": parse_addresses(message, "Bcc"),
        "reply_to": parse_addresses(message, "Reply-To"),
        "in_reply_to": decode_header_value(message.get("In-Reply-To")),
        "references": parse_references(message),
        "subject": decode_header_value(message.get("Subject")),
        "body_text": body_text,
        "attachments": attachments,
    }
    if include_html:
        data["body_html"] = body_html
    return data, warnings
