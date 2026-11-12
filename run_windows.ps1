$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Ejecuta primero .\setup_windows.ps1" }

$port = $env:PORT
if (-not $port) { $port = "5000" }
$envFile = Join-Path $PSScriptRoot ".env"
if (-not $env:PORT -and (Test-Path $envFile)) {
    $portLine = Select-String -Path $envFile -Pattern '^\s*PORT\s*=\s*(\d+)\s*$' | Select-Object -First 1
    if ($portLine -and $portLine.Matches[0].Groups[1].Success) {
        $port = $portLine.Matches[0].Groups[1].Value
    }
}
Write-Host "WA-Bridge AI: http://localhost:$port" -ForegroundColor Cyan
Write-Host "Asegúrate de que Ollama esté ejecutándose para usar Qwen."
& $python "run.py"
if ($LASTEXITCODE -ne 0) {
    throw "WA-Bridge AI terminó con un error (código $LASTEXITCODE). Revisa el mensaje anterior."
}
