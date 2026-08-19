from datetime import UTC, datetime
from pathlib import Path

from preparador_dados_ia.contracts.text import TextHeading, build_text_document_record
from preparador_dados_ia.core.cancellation import CancellationToken
from preparador_dados_ia.core.partitioning import PartitionLimits
from preparador_dados_ia.outputs.markdown import MarkdownDocumentWriter

CONVERTED_AT = datetime(2026, 8, 6, 9, 30, tzinfo=UTC)


def test_plain_text_is_represented_as_markdown_with_local_metadata(tmp_path: Path) -> None:
    record = build_text_document_record(
        source_file="relatorio.txt",
        source_file_type="txt",
        source_size_bytes=30,
        encoding="utf-8",
        content="RELATÓRIO\n\nConteúdo local.",
        title="RELATÓRIO",
        headings=[TextHeading(level=1, text="RELATÓRIO", line_number=1)],
        converted_at=CONVERTED_AT,
    )
    writer = MarkdownDocumentWriter(tmp_path, PartitionLimits(10_000, 5_000))

    segments, oversized = writer.add(record, CancellationToken())

    output = (tmp_path / writer.parts[0].file).read_text(encoding="utf-8")
    assert segments == 1
    assert oversized is False
    assert output.startswith('---\nschema_version: "1.0"')
    assert 'source_file: "relatorio.txt"' in output
    assert "# RELATÓRIO" in output
    assert "Conteúdo local." in output
    assert "C:\\" not in output


def test_large_markdown_is_split_into_bounded_standalone_parts(tmp_path: Path) -> None:
    content = "\n\n".join(f"## Seção {index}\n" + ("conteúdo local " * 18) for index in range(12))
    record = build_text_document_record(
        source_file="manual.md",
        source_file_type="markdown",
        source_size_bytes=len(content.encode("utf-8")),
        encoding="utf-8",
        content=content,
        converted_at=CONVERTED_AT,
    )
    limits = PartitionLimits(max_bytes=900, max_tokens=450)
    writer = MarkdownDocumentWriter(tmp_path, limits)

    segments, oversized = writer.add(record, CancellationToken())

    assert segments > 1
    assert oversized is False
    for part in writer.parts:
        path = tmp_path / part.file
        output = path.read_text(encoding="utf-8")
        assert path.stat().st_size <= limits.max_bytes
        assert output.startswith("---\n")
        assert "segment_number:" in output
        assert f"segment_count: {segments}" in output
