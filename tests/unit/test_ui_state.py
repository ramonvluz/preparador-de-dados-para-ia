from pathlib import Path

import pytest

from preparador_dados_ia.application.conversion import DestinationProfile
from preparador_dados_ia.ui.state import (
    DesktopConversionRequest,
    UiProfile,
    human_duration,
    human_file_size,
    recommendation_for,
)


def test_profile_recommendations_map_to_core_profiles() -> None:
    platform = recommendation_for(UiProfile.PLATFORM)
    api = recommendation_for(UiProfile.API)

    assert platform.format_name == "JSON particionado"
    assert api.format_name == "JSONL particionado"
    assert UiProfile.PLATFORM.destination_profile is DestinationProfile.PLATFORM
    assert UiProfile.API.destination_profile is DestinationProfile.API


def test_text_sources_always_recommend_markdown(tmp_path: Path) -> None:
    source = tmp_path / "manual.txt"

    platform = recommendation_for(UiProfile.PLATFORM, source)
    api = recommendation_for(UiProfile.API, source)

    assert platform.format_name == "Markdown particionado"
    assert api.format_name == "Markdown particionado"


def test_desktop_request_validates_source_and_builds_settings(tmp_path: Path) -> None:
    source = tmp_path / "artificial.mbox"
    source.write_text("From artificial@example.invalid\n", encoding="utf-8")
    request = DesktopConversionRequest(
        source=source,
        output_root=tmp_path / "saida",
        profile=UiProfile.API,
        include_html=True,
    )

    request.validate()
    assert request.settings.profile is DestinationProfile.API
    assert request.settings.include_html is True


def test_desktop_request_rejects_unsupported_extension(tmp_path: Path) -> None:
    source = tmp_path / "artificial.xls"
    source.write_text("artificial", encoding="utf-8")
    request = DesktopConversionRequest(source=source, output_root=tmp_path)

    with pytest.raises(ValueError, match="MBOX, TXT, Markdown, PDF, DOCX, CSV ou XLSX"):
        request.validate()


def test_pdf_source_recommends_markdown_with_page_titles(tmp_path: Path) -> None:
    source = tmp_path / "artificial.pdf"

    recommendation = recommendation_for(UiProfile.PLATFORM, source)

    assert recommendation.format_name == "Markdown com páginas"
    assert "títulos de página" in recommendation.explanation


def test_word_source_recommends_structured_markdown(tmp_path: Path) -> None:
    source = tmp_path / "artificial.docx"

    recommendation = recommendation_for(UiProfile.API, source)

    assert recommendation.format_name == "Markdown estruturado"
    assert "tabelas simples" in recommendation.explanation


def test_csv_source_recommends_profile_specific_tabular_format(tmp_path: Path) -> None:
    source = tmp_path / "artificial.csv"

    platform = recommendation_for(UiProfile.PLATFORM, source)
    api = recommendation_for(UiProfile.API, source)

    assert platform.format_name == "JSON tabular"
    assert api.format_name == "JSONL tabular"


def test_desktop_request_accepts_csv_and_ignores_html(tmp_path: Path) -> None:
    source = tmp_path / "artificial.csv"
    source.write_text("Código,Valor\n1,10\n", encoding="utf-8")
    request = DesktopConversionRequest(source=source, output_root=tmp_path, include_html=True)

    request.validate()

    assert request.settings.include_html is False


def test_xlsx_source_recommends_profile_specific_spreadsheet_format(tmp_path: Path) -> None:
    source = tmp_path / "artificial.xlsx"

    platform = recommendation_for(UiProfile.PLATFORM, source)
    api = recommendation_for(UiProfile.API, source)

    assert platform.format_name == "JSON de planilha"
    assert api.format_name == "JSONL de planilha"
    assert "fórmulas" in platform.explanation


def test_desktop_request_accepts_xlsx_and_ignores_html(tmp_path: Path) -> None:
    source = tmp_path / "artificial.xlsx"
    source.write_bytes(b"artificial")
    request = DesktopConversionRequest(source=source, output_root=tmp_path, include_html=True)

    request.validate()

    assert request.settings.include_html is False


@pytest.mark.parametrize("suffix", [".txt", ".md", ".markdown"])
def test_desktop_request_accepts_text_formats_and_ignores_html(
    tmp_path: Path,
    suffix: str,
) -> None:
    source = tmp_path / f"artificial{suffix}"
    source.write_text("# Artificial", encoding="utf-8")
    request = DesktopConversionRequest(source=source, output_root=tmp_path, include_html=True)

    request.validate()

    assert request.settings.include_html is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (512, "512 bytes"),
        (1536, "1.50 KB"),
        (2 * 1024 * 1024, "2.00 MB"),
    ],
)
def test_human_file_size(value: int, expected: str) -> None:
    assert human_file_size(value) == expected


def test_human_duration() -> None:
    assert human_duration(12.2) == "12 s"
    assert human_duration(323.9) == "5 min 24 s"
