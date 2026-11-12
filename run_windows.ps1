$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Ejecuta primero .\setup_windows.ps1" }
Write-Host "WA-Bridge AI: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "Asegúrate de que Ollama esté ejecutándose para usar Qwen."
& $python "run.py"
