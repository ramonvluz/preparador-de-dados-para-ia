from pathlib import Path

from limebh_preparador.cli import main

PROJECT_ROOT = Path(__file__).parents[2]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "artificial_emails.mbox"
PDF_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "artificial_document.pdf"


def test_cli_is_a_client_of_the_core(tmp_path: Path, capsys: object) -> None:
    output = tmp_path / "cli"
    exit_code = main([str(FIXTURE), "--output", str(output), "--profile", "api"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "2/2 mensagens" in captured.out
    assert list((output / "PRONTO_PARA_IA").glob("*.jsonl"))


def test_cli_dispatches_text_sources_to_markdown(tmp_path: Path, capsys: object) -> None:
    source = tmp_path / "manual.txt"
    source.write_text("MANUAL\n\nConteúdo local.", encoding="utf-8")
    output = tmp_path / "texto_cli"

    exit_code = main([str(source), "--output", str(output), "--profile", "api"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "1/1 documento" in captured.out
    assert list((output / "PRONTO_PARA_IA").glob("*.md"))


def test_cli_dispatches_pdf_sources_to_page_marked_markdown(
    tmp_path: Path,
    capsys: object,
) -> None:
    output = tmp_path / "pdf_cli"

    exit_code = main([str(PDF_FIXTURE), "--output", str(output)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "3/3 páginas" in captured.out
    assert list((output / "PRONTO_PARA_IA").glob("*.md"))
