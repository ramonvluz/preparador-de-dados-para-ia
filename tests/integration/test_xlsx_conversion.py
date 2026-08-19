import hashlib
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.worksheet.table import Table

from preparador_dados_ia.application.conversion import ConversionSettings, DestinationProfile
from preparador_dados_ia.application.service import convert_source


def _source(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Dados"
    sheet.append(["Código", "Valor", "Dobro"])
    sheet.append(["001", 10, "=B2*2"])
    sheet.append(["002", 20, "=B3*2"])
    sheet.add_table(Table(displayName="DadosPrincipais", ref="A1:C3"))
    workbook.save(path)
    workbook.close()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_xlsx_conversion_generates_json_and_auditable_report(tmp_path: Path) -> None:
    source = tmp_path / "dados.xlsx"
    _source(source)
    source_hash = _sha256(source)
    output = tmp_path / "resultado"

    report = convert_source(source, output)

    assert _sha256(source) == source_hash
    assert report["converted_records"] == 2
    assert report["sources"][0]["detected_format"] == "xlsx"
    assert report["spreadsheet_extraction"]["sheets"] == 1
    assert report["spreadsheet_extraction"]["tables"] == 1
    assert report["spreadsheet_extraction"]["formulas"] == 2
    assert report["spreadsheet_extraction"]["external_links_followed"] is False
    part = output / "PRONTO_PARA_IA" / report["parts"][0]["file"]
    records = json.loads(part.read_text(encoding="utf-8"))
    assert records[0]["source"] == source.name
    assert records[0]["sheet"] == "Dados"
    assert records[0]["columns"] == ["C\u00f3digo", "Valor", "Dobro"]
    assert records[0]["formulas"][0]["cell"] == "C2"
    assert "record_type" not in records[0]
    assert "Tipo identificado: XLSX" in (output / "LEIA-ME.txt").read_text(encoding="utf-8")


def test_xlsx_api_profile_generates_jsonl(tmp_path: Path) -> None:
    source = tmp_path / "dados.xlsx"
    _source(source)
    output = tmp_path / "api"

    report = convert_source(
        source,
        output,
        settings=ConversionSettings(profile=DestinationProfile.API),
    )

    assert report["output_format"] == "jsonl"
    part = output / "PRONTO_PARA_IA" / report["parts"][0]["file"]
    assert all(
        "sheet" in json.loads(line) for line in part.read_text(encoding="utf-8").splitlines()
    )
