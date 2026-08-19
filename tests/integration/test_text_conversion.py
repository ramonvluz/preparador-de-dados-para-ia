import hashlib
from pathlib import Path

import pytest

from preparador_dados_ia.application.conversion import ConversionSettings, DestinationProfile
from preparador_dados_ia.application.progress import ConversionProgress
from preparador_dados_ia.application.service import convert_source
from preparador_dados_ia.core.cancellation import CancellationToken


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_txt_conversion_generates_clean_markdown_and_auditable_report(tmp_path: Path) -> None:
    source = tmp_path / "orientacoes.txt"
    source.write_text(
        "ORIENTAÇÕES\n\nEspaço\u00a0local e marca\u200binvisível.\u2028Nova linha.\n",
        encoding="utf-8",
    )
    source_hash = _sha256(source)
    output = tmp_path / "resultado"

    report = convert_source(source, output)

    assert _sha256(source) == source_hash
    assert report["result"] == "success"
    assert report["output_format"] == "markdown"
    assert report["converted_records"] == 1
    assert report["failed_records"] == 0
    assert report["text_extraction"]["encoding"] == "utf-8"
    assert report["unicode_cleanup"]["total_changes"] == 3
    ready_files = list((output / "PRONTO_PARA_IA").glob("*.md"))
    assert len(ready_files) == 1
    ready_text = ready_files[0].read_text(encoding="utf-8")
    assert "# ORIENTAÇÕES" in ready_text
    assert "Espaço local e marcal invisível." not in ready_text
    assert "Espaço local e marcainvisível." in ready_text
    assert "Nova linha." in ready_text
    assert str(source.resolve()) not in ready_text
    assert (output / "LEIA-ME.txt").is_file()
    assert (output / "relatorio_conversao.json").is_file()

    with pytest.raises(FileExistsError):
        convert_source(source, output)


def test_markdown_is_preserved_for_api_profile_and_partitioned(tmp_path: Path) -> None:
    source = tmp_path / "manual.md"
    source.write_text("# Manual\n\n" + ("Conteúdo semântico.\n\n" * 80), encoding="utf-8")
    output = tmp_path / "api"

    report = convert_source(
        source,
        output,
        settings=ConversionSettings(
            profile=DestinationProfile.API,
            max_size_mb=0.001,
            max_tokens=500,
        ),
    )

    assert report["profile"] == "api"
    assert report["output_format"] == "markdown"
    assert report["segmented_records"] == 1
    assert len(report["parts"]) > 1
    for part in report["parts"]:
        path = output / "PRONTO_PARA_IA" / part["file"]
        assert path.suffix == ".md"
        assert path.stat().st_size <= report["settings"]["max_bytes"]


def test_windows_1252_text_is_decoded_without_corrupting_portuguese(tmp_path: Path) -> None:
    content = (
        "RELATÓRIO\r\n\r\nContratação, manutenção, ação, órgão, informações e seção.\r\n"
    ) * 8
    source = tmp_path / "legado.txt"
    source.write_bytes(content.encode("cp1252"))

    report = convert_source(source, tmp_path / "legado_saida")

    ready = tmp_path / "legado_saida" / "PRONTO_PARA_IA" / report["parts"][0]["file"]
    output = ready.read_text(encoding="utf-8")
    assert "Contratação, manutenção, ação, órgão, informações e seção." in output
    assert report["text_extraction"]["encoding"] == "cp1252"
    assert report["result"] == "success_with_warnings"


def test_text_cancellation_keeps_report_and_only_complete_parts(tmp_path: Path) -> None:
    source = tmp_path / "cancelar.txt"
    source.write_text("Conteúdo local.\n" * 100, encoding="utf-8")
    token = CancellationToken()

    def cancel_while_preparing(progress: ConversionProgress) -> None:
        if progress.stage == "preparing":
            token.cancel()

    output = tmp_path / "cancelado"
    report = convert_source(
        source,
        output,
        cancellation_token=token,
        progress_callback=cancel_while_preparing,
    )

    assert report["result"] == "cancelled"
    assert report["converted_records"] == 0
    assert list(output.rglob("*.tmp")) == []
    assert (output / "relatorio_conversao.json").is_file()
    assert (output / "LEIA-ME.txt").is_file()
