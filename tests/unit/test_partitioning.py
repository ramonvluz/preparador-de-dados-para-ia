import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from preparador_dados_ia.contracts.email import build_email_record
from preparador_dados_ia.core.partitioning import (
    PartitionLimits,
    record_metrics,
    split_oversized_record,
)
from preparador_dados_ia.outputs.parts import OutputFormat, PartWriter


def _record(body: str, message_id: str = "<artificial@example.invalid>") -> dict[str, object]:
    return build_email_record(
        {
            "message_id": message_id,
            "thread_id": None,
            "gmail_labels": [],
            "date": "2026-08-05T12:00:00+00:00",
            "date_raw": "Wed, 05 Aug 2026 12:00:00 +0000",
            "from": [],
            "to": [],
            "cc": [],
            "bcc": [],
            "reply_to": [],
            "in_reply_to": None,
            "references": [],
            "subject": "Artificial",
            "body_text": body,
            "attachments": [],
        },
        source_file="artificial.mbox",
        source_size_bytes=10_000,
        converted_at=datetime(2026, 8, 5, 12, 0, tzinfo=UTC),
    )


def test_oversized_body_is_segmented_with_link_preserved() -> None:
    limits = PartitionLimits(max_bytes=1100, max_tokens=550)
    original = _record("conteúdo artificial " * 300)

    segments, remains_oversized = split_oversized_record(original, limits)

    assert remains_oversized is False
    assert len(segments) > 1
    assert {item["record_id"] for item in segments} == {original["record_id"]}
    assert [item["processing"]["segment_number"] for item in segments] == list(
        range(1, len(segments) + 1)
    )
    assert all(item["processing"]["segment_count"] == len(segments) for item in segments)
    assert all(record_metrics(item)[1] <= limits.max_bytes for item in segments)
    assert all(record_metrics(item)[2] <= limits.max_tokens for item in segments)


@pytest.mark.parametrize("output_format", [OutputFormat.JSON, OutputFormat.JSONL])
def test_part_writer_produces_valid_bounded_files(
    tmp_path: Path,
    output_format: OutputFormat,
) -> None:
    limits = PartitionLimits(max_bytes=2200, max_tokens=1100)
    writer = PartWriter(tmp_path, limits, output_format)
    for index in range(5):
        writer.add(_record("texto " * 30, f"<artificial-{index}@example.invalid>"))
    writer.flush()

    assert len(writer.parts) > 1
    for part in writer.parts:
        path = tmp_path / part.file
        assert path.stat().st_size <= limits.max_bytes
        assert part.estimated_tokens <= limits.max_tokens
        if output_format is OutputFormat.JSON:
            assert isinstance(json.loads(path.read_text(encoding="utf-8")), list)
        else:
            lines = path.read_text(encoding="utf-8").splitlines()
            assert lines
            assert all(json.loads(line)["record_type"] == "email_message" for line in lines)
