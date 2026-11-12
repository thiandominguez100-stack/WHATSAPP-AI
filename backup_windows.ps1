$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $python) {
    & $python "scripts\backup_db.py"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py "scripts\backup_db.py"
} else {
    throw "No se encontró Python. Ejecuta primero .\setup_windows.ps1."
}

if ($LASTEXITCODE -ne 0) {
    throw "No se pudo completar la copia de seguridad."
}
