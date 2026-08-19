from datetime import UTC, datetime
from pathlib import Path

from preparador_dados_ia.contracts.pdf import PdfPage, build_pdf_document_record
from preparador_dados_ia.core.cancellation import CancellationToken
from preparador_dados_ia.core.partitioning import PartitionLimits
from preparador_dados_ia.outputs.pdf_markdown import PdfMarkdownWriter

CONVERTED_AT = datetime(2026, 8, 6, 13, 30, tzinfo=UTC)


def _record(*pages: PdfPage) -> dict[str, object]:
    return build_pdf_document_record(
        source_file="relatorio.pdf",
        source_size_bytes=2048,
        title="Relatorio artificial",
        author="Projeto Artificial",
        pages=pages,
        converted_at=CONVERTED_AT,
    )


def test_pdf_markdown_preserves_explicit_page_boundaries(tmp_path: Path) -> None:
    record = _record(
        PdfPage(1, "Conteudo da primeira pagina.", "embedded_text"),
        PdfPage(2, "", "none"),
    )
    writer = PdfMarkdownWriter(tmp_path, PartitionLimits(20_000, 10_000))

    segments, oversized = writer.add(record, CancellationToken())

    output = (tmp_path / writer.parts[0].file).read_text(encoding="utf-8")
    assert segments == 1
    assert oversized is False
    assert "<!-- PREPARADOR_PDF_CATALOG -->" in output
    assert "<!-- PREPARADOR_PAGE_START page=1 -->" in output
    assert "<!-- PREPARADOR_PAGE_END page=1 -->" in output
    assert "<!-- PREPARADOR_PAGE_START page=2 -->" in output
    assert "OCR não foi aplicado" in output
    assert "page_start: 1" in output
    assert "page_end: 2" in output


def test_oversized_pdf_page_is_segmented_into_bounded_parts(tmp_path: Path) -> None:
    record = _record(PdfPage(1, "Paragrafo artificial. " * 400, "embedded_text"))
    limits = PartitionLimits(max_bytes=1_400, max_tokens=700)
    writer = PdfMarkdownWriter(tmp_path, limits)

    segments, oversized = writer.add(record, CancellationToken())

    assert segments > 2
    assert oversized is False
    page_parts = 0
    for part in writer.parts:
        path = tmp_path / part.file
        output = path.read_text(encoding="utf-8")
        assert path.stat().st_size <= limits.max_bytes
        if "PREPARADOR_PAGE_START" in output:
            page_parts += 1
            assert "segment=" in output
            assert "PREPARADOR_PAGE_END" in output
    assert page_parts > 1
