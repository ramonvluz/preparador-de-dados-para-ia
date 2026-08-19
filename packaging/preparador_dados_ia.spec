from pathlib import Path


project_root = Path(SPECPATH).parent
source_root = project_root / "src"
assets = source_root / "preparador_dados_ia" / "assets"

a = Analysis(
    [str(source_root / "preparador_dados_ia" / "ui" / "__main__.py")],
    pathex=[str(source_root)],
    binaries=[],
    datas=[(str(assets), "preparador_dados_ia/assets")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["jsonschema", "PIL", "pytest", "reportlab", "ruff"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Preparador de Dados para IA",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(assets / "app_icon.ico"),
    version=str(project_root / "packaging" / "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Preparador de Dados para IA",
)
