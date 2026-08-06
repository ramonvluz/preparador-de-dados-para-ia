import hashlib
from pathlib import Path

from limebh_preparador.application.progress import ConversionProgress
from limebh_preparador.application.service import convert_source
from limebh_preparador.core.cancellation import CancellationToken

PROJECT_ROOT = Path(__file__).parents[2]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "artificial_document.docx"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_word_conversion_generates_structured_markdown_and_audit_report(
    tmp_path: Path,
) -> None:
    source_hash = _sha256(FIXTURE)
    output = tmp_path / "word_saida"

    report = convert_source(FIXTURE, output)

    assert _sha256(FIXTURE) == source_hash
    assert report["result"] == "success_with_warnings"
    assert report["converted_records"] == 1
    assert report["failed_records"] == 0
    assert report["word_extraction"] == {
        "block_count": 18,
        "paragraphs": 7,
        "headings": 5,
        "list_items": 5,
        "tables": 1,
        "sections": 5,
    }
    assert report["omitted_content"] == {
        "images": 1,
        "headers_footers": True,
        "advanced_features": [],
        "external_references_downloaded": False,
    }
    ready_files = list((output / "PRONTO_PARA_IA").glob("*.md"))
    assert ready_files
    ready_text = "\n".join(path.read_text(encoding="utf-8") for path in ready_files)
    assert "Guia Artificial de Validação 3D" in ready_text
    assert "# 1. Objetivo" in ready_text
    assert "    - Subitem artificial para validar nível." in ready_text
    assert "Risco \\| mitigação" in ready_text
    assert "IMAGEM ARTIFICIAL" not in ready_text
    assert str(FIXTURE.resolve()) not in ready_text
    assert (output / "LEIA-ME.txt").is_file()
    assert (output / "relatorio_conversao.json").is_file()


def test_invalid_docx_fails_without_exposing_content(tmp_path: Path) -> None:
    source = tmp_path / "invalido.docx"
    source.write_text("segredo-artificial-fora-de-um-pacote", encoding="utf-8")
    output = tmp_path / "invalido_saida"

    report = convert_source(source, output)

    assert report["result"] == "failure"
    assert report["errors"][0]["error_type"] == "InvalidDocxError"
    report_text = (output / "relatorio_conversao.json").read_text(encoding="utf-8")
    assert "segredo-artificial-fora-de-um-pacote" not in report_text


def test_word_cancellation_keeps_only_complete_artifacts(tmp_path: Path) -> None:
    token = CancellationToken()

    def cancel_after_first_block(progress: ConversionProgress) -> None:
        if progress.stage == "converting" and progress.current == 1:
            token.cancel()

    output = tmp_path / "word_cancelado"
    report = convert_source(
        FIXTURE,
        output,
        cancellation_token=token,
        progress_callback=cancel_after_first_block,
    )

    assert report["result"] == "cancelled"
    assert report["converted_records"] == 0
    assert list(output.rglob("*.tmp")) == []
    assert (output / "LEIA-ME.txt").is_file()
    assert (output / "relatorio_conversao.json").is_file()
