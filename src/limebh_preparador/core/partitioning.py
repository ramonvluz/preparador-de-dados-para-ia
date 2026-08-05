from __future__ import annotations

import json
from dataclasses import dataclass

from limebh_preparador.core.cleaning import html_to_text


@dataclass(frozen=True, slots=True)
class PartitionLimits:
    max_bytes: int
    max_tokens: int

    def __post_init__(self) -> None:
        if self.max_bytes <= 0 or self.max_tokens <= 0:
            raise ValueError("Os limites de bytes e tokens devem ser maiores que zero.")


def json_text(record: dict[str, object]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def estimate_tokens(value: str) -> int:
    """Estima conservadoramente ao menos um token para cada dois bytes UTF-8."""

    return max(1, (len(value.encode("utf-8")) + 1) // 2)


def record_metrics(record: dict[str, object]) -> tuple[str, int, int]:
    serialized = json_text(record)
    return serialized, len(serialized.encode("utf-8")), estimate_tokens(serialized)


def split_oversized_record(
    record: dict[str, object], limits: PartitionLimits
) -> tuple[list[dict[str, object]], bool]:
    """Segmenta o corpo de uma mensagem sem quebrar o vínculo do registro."""

    _, size, tokens = record_metrics(record)
    if size <= limits.max_bytes and tokens <= limits.max_tokens:
        return [record], False

    data = record.get("data")
    if not isinstance(data, dict):
        return [record], True

    body = str(data.get("body_text") or "")
    html_body = data.get("body_html")
    if not body and html_body:
        body = html_to_text(str(html_body))

    base = dict(record)
    base_data = dict(data)
    base_data.pop("body_html", None)
    base_data["body_text"] = ""
    base["data"] = base_data

    processing = dict(base.get("processing") or {})
    processing["warnings"] = list(processing.get("warnings") or []) + [
        "oversized_message_segmented"
    ]
    base["processing"] = processing
    if not body:
        return [record], True

    segments: list[str] = []
    position = 0
    while position < len(body):
        low, high, best = 1, len(body) - position, 0
        while low <= high:
            middle = (low + high) // 2
            candidate = dict(base)
            candidate["data"] = dict(
                base_data,
                body_text=body[position : position + middle],
            )
            candidate["processing"] = dict(
                processing,
                segment_number=len(segments) + 1,
                segment_count=999_999,
            )
            _, candidate_size, candidate_tokens = record_metrics(candidate)
            if candidate_size <= limits.max_bytes and candidate_tokens <= limits.max_tokens:
                best = middle
                low = middle + 1
            else:
                high = middle - 1

        if best == 0:
            return [record], True
        segments.append(body[position : position + best])
        position += best

    output: list[dict[str, object]] = []
    for number, segment in enumerate(segments, start=1):
        item = dict(base)
        item["data"] = dict(base_data, body_text=segment)
        item["processing"] = dict(
            processing,
            segment_number=number,
            segment_count=len(segments),
        )
        output.append(item)
    return output, False
