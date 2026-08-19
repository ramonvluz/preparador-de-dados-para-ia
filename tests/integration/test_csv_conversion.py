import hashlib
import json
from pathlib import Path

from preparador_dados_ia.application.conversion import ConversionSettings, DestinationProfile
from preparador_dados_ia.application.service import convert_source


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_csv_conversion_generates_typed_json_and_auditable_report(tmp_path: Path) -> None:
    source = tmp_path / "clientes.csv"
    source.write_text(
        "ID;Cliente;Receita;Ativo;Data\n"
        "001;Empresa Exemplo;1250,50;sim;2026-08-01\n"
        "2;Instituto Exemplo;;não;2026-08-02\n",
        encoding="utf-8",
    )
    source_hash = _sha256(source)
    output = tmp_path / "resultado"

    report = convert_source(source, output)

    assert _sha256(source) == source_hash
    assert report["result"] == "success"
    assert report["output_format"] == "json"
    assert report["converted_records"] == 2
    assert report["tabular_extraction"]["columns"] == 5
    part = output / "PRONTO_PARA_IA" / report["parts"][0]["file"]
    records = json.loads(part.read_text(encoding="utf-8"))
    assert records[0]["record_type"] == "tabular_dataset"
    assert records[0]["data"]["dataset"]["rows"][0][0] == "001"
    assert "Tipo identificado: CSV" in (output / "LEIA-ME.txt").read_text(encoding="utf-8")
    assert (output / "relatorio_conversao.json").is_file()


def test_csv_api_profile_generates_valid_jsonl(tmp_path: Path) -> None:
    source = tmp_path / "dados.csv"
    source.write_text("Código,Valor\n1,10\n2,20\n", encoding="utf-8")
    output = tmp_path / "api"

    report = convert_source(
        source,
        output,
        settings=ConversionSettings(profile=DestinationProfile.API),
    )

    assert report["profile"] == "api"
    assert report["output_format"] == "jsonl"
    part = output / "PRONTO_PARA_IA" / report["parts"][0]["file"]
    lines = part.read_text(encoding="utf-8").splitlines()
    assert lines
    assert all(json.loads(line)["record_type"] == "tabular_dataset" for line in lines)
