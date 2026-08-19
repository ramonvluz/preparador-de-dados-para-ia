import hashlib
from pathlib import Path

from pypdf import PdfWriter

from preparador_dados_ia.application.service import convert_source

PROJECT_ROOT = Path(__file__).parents[2]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "artificial_document.pdf"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pdf_conversion_generates_page_marked_markdown_and_audit_report(
    tmp_path: Path,
) -> None:
    source_hash = _sha256(FIXTURE)
    output = tmp_path / "pdf_saida"

    report = convert_source(FIXTURE, output)

    assert _sha256(FIXTURE) == source_hash
    assert report["result"] == "success_with_warnings"
    assert report["output_format"] == "markdown"
    assert report["converted_records"] == 1
    assert report["failed_records"] == 0
    assert report["pdf_extraction"] == {
        "page_count": 3,
        "pages_with_text": 2,
        "pages_without_text": 1,
        "outline_items": 4,
        "embedded_files_catalogued": 1,
        "images_catalogued": 1,
        "ocr_applied": False,
    }
    assert report["omitted_content"] == {
        "embedded_file_binaries": 1,
        "image_binaries": 1,
        "ocr_not_applied": True,
        "external_references_downloaded": False,
    }
    ready_files = list((output / "PRONTO_PARA_IA").glob("*.md"))
    assert ready_files
    ready_text = "\n".join(path.read_text(encoding="utf-8") for path in ready_files)
    assert "Relatorio Artificial da Fase 3C" in ready_text
    assert "<!-- PREPARADOR_PAGE_START page=1 -->" in ready_text
    assert "<!-- PREPARADOR_PAGE_START page=3 -->" in ready_text
    assert "notas_artificiais.txt" in ready_text
    assert str(FIXTURE.resolve()) not in ready_text
    assert (output / "LEIA-ME.txt").is_file()
    assert (output / "relatorio_conversao.json").is_file()


def test_password_protected_pdf_fails_without_exposing_content(tmp_path: Path) -> None:
    source = tmp_path / "protegido.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    writer.add_metadata({"/Title": "PDF protegido artificial"})
    writer.encrypt("segredo-artificial")
    with source.open("wb") as stream:
        writer.write(stream)

    output = tmp_path / "protegido_saida"
    report = convert_source(source, output)

    assert report["result"] == "failure"
    assert report["converted_records"] == 0
    assert report["failed_records"] == 1
    assert report["errors"][0]["error_type"] == "PdfReadError"
    assert list((output / "PRONTO_PARA_IA").glob("*.md")) == []
    assert "segredo-artificial" not in (output / "relatorio_conversao.json").read_text(
        encoding="utf-8"
    )
