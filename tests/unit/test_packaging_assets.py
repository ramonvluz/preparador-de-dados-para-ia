from pathlib import Path

from preparador_dados_ia import __version__

PROJECT_ROOT = Path(__file__).parents[2]
ASSETS = PROJECT_ROOT / "src" / "preparador_dados_ia" / "assets"


def test_application_icons_exist_with_expected_signatures() -> None:
    png = ASSETS / "app_icon.png"
    ico = ASSETS / "app_icon.ico"

    assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert ico.read_bytes().startswith(b"\x00\x00\x01\x00")


def test_portable_build_files_reference_current_version() -> None:
    build_script = (PROJECT_ROOT / "scripts" / "build_portable.ps1").read_text(encoding="utf-8")
    version_info = (PROJECT_ROOT / "packaging" / "version_info.txt").read_text(encoding="utf-8")

    assert __version__ in build_script
    assert f"FileVersion', '{__version__}'" in version_info
