from datetime import UTC, datetime
from pathlib import Path

from preparador_dados_ia.contracts.word import (
    WordHeading,
    WordListItem,
    WordParagraph,
    WordTable,
    build_word_document_record,
)
from preparador_dados_ia.core.cancellation import CancellationToken
from preparador_dados_ia.core.partitioning import PartitionLimits
from preparador_dados_ia.outputs.word_markdown import WordMarkdownWriter

CONVERTED_AT = datetime(2026, 8, 6, 16, 0, tzinfo=UTC)


def _record(*blocks: object) -> dict[str, object]:
    return build_word_document_record(
        source_file="guia.docx",
        source_size_bytes=4096,
        title="Guia artificial",
        author="Projeto Artificial",
        blocks=blocks,
        converted_at=CONVERTED_AT,
    )


def test_word_markdown_preserves_headings_lists_tables_and_block_references(
    tmp_path: Path,
) -> None:
    record = _record(
        WordHeading("Orientações", 1),
        WordParagraph("Conteúdo local.", "Normal"),
        WordListItem("Item principal", 0, False),
        WordListItem("Subitem", 1, False),
        WordTable(
            rows=(("Risco", "Mitigação"), ("A | B", "Controle local")),
            has_header=True,
        ),
    )
    writer = WordMarkdownWriter(tmp_path, PartitionLimits(20_000, 10_000))

    segments, oversized = writer.add(record, CancellationToken())

    output = (tmp_path / writer.parts[0].file).read_text(encoding="utf-8")
    assert segments == 1
    assert oversized is False
    assert output.startswith("> Fonte: guia.docx\n\n")
    assert "# Orientações" in output
    assert "- Item principal\n    - Subitem" in output
    assert "| Risco | Mitigação |" in output
    assert "| A \\| B | Controle local |" in output
    assert "PREPARADOR_" not in output
    assert "schema_version" not in output


def test_large_word_paragraph_is_segmented_into_bounded_parts(tmp_path: Path) -> None:
    record = _record(WordParagraph("Parágrafo artificial. " * 400, "Normal"))
    limits = PartitionLimits(max_bytes=1_400, max_tokens=700)
    writer = WordMarkdownWriter(tmp_path, limits)

    segments, oversized = writer.add(record, CancellationToken())

    assert segments > 2
    assert oversized is False
    for part in writer.parts:
        path = tmp_path / part.file
        output = path.read_text(encoding="utf-8")
        assert path.stat().st_size <= limits.max_bytes
        if "Trecho" in output:
            assert f"/{segments}" in output
