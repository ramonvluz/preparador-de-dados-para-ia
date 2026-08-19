$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$spec = Join-Path $projectRoot "packaging\preparador_dados_ia.spec"
$bundle = Join-Path $projectRoot "dist\Preparador de Dados para IA"
$archive = Join-Path $projectRoot "dist\Preparador-de-Dados-para-IA-portatil-0.1.0-windows-x64.zip"
$checksums = Join-Path $projectRoot "dist\SHA256SUMS.txt"
$manual = Join-Path $projectRoot "docs\MANUAL_RAPIDO.md"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Ambiente virtual não encontrado em $python"
}
if (-not (Test-Path -LiteralPath $spec)) {
    throw "Configuração do PyInstaller não encontrada em $spec"
}

& $python "$projectRoot\scripts\create_app_icon.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m PyInstaller --noconfirm --clean $spec
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path -LiteralPath $bundle)) {
    throw "O pacote portátil não foi criado em $bundle"
}

Copy-Item -LiteralPath $manual -Destination (Join-Path $bundle "LEIA-ME.md") -Force

if (Test-Path -LiteralPath $archive) {
    Remove-Item -LiteralPath $archive -Force
}
Compress-Archive -LiteralPath $bundle -DestinationPath $archive -CompressionLevel Optimal

$hash = Get-FileHash -LiteralPath $archive -Algorithm SHA256
"$($hash.Hash)  $($hash.Path | Split-Path -Leaf)" | Set-Content -LiteralPath $checksums -Encoding ascii

[PSCustomObject]@{
    Executable = Join-Path $bundle "Preparador de Dados para IA.exe"
    PortableZip = $archive
    Sha256 = $hash.Hash
}
