$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Ambiente virtual não encontrado em $python"
}

& $python -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m ruff format --check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m compileall -q src tests
exit $LASTEXITCODE
