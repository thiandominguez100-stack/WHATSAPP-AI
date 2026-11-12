$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

$failed = $false
function Check-Result([string]$Name, [bool]$Ok, [string]$Detail) {
    if ($Ok) {
        Write-Host "[OK]   $Name - $Detail" -ForegroundColor Green
    } else {
        Write-Host "[FALTA] $Name - $Detail" -ForegroundColor Yellow
        $script:failed = $true
    }
}

Write-Host "== WA-Bridge AI: diagnóstico local ==" -ForegroundColor Cyan
Write-Host "Este diagnóstico no modifica archivos ni descarga modelos."
Write-Host ""

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    $versionText = & py --version 2>&1
    $versionOk = $LASTEXITCODE -eq 0
    Check-Result "Python" $versionOk "$versionText"
} else {
    Check-Result "Python" $false "No se encontró el lanzador 'py'. Instala Python 3.10 o superior."
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
Check-Result "Entorno virtual" (Test-Path $venvPython) "Se busca .venv\Scripts\python.exe; si falta, ejecuta .\setup_windows.ps1"

$envFile = Join-Path $PSScriptRoot ".env"
Check-Result "Configuración .env" (Test-Path $envFile) "Se busca el archivo .env; no se muestran sus valores."

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
    $modelList = & ollama list 2>&1 | Out-String
    $ollamaOk = $LASTEXITCODE -eq 0
    Check-Result "Ollama CLI" $ollamaOk "Se pudo consultar ollama list."
    $modelOk = $ollamaOk -and ($modelList -match "(?m)^qwen2\.5:1\.5b\s")
    Check-Result "Modelo Qwen" $modelOk "Se busca qwen2.5:1.5b; no se descarga automáticamente."
} else {
    Check-Result "Ollama CLI" $false "No se encontró ollama en PATH."
    Check-Result "Modelo Qwen" $false "No se pudo comprobar el modelo."
}

try {
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3
    Check-Result "Servicio Ollama" $true "Responde en 127.0.0.1:11434."
} catch {
    Check-Result "Servicio Ollama" $false "No responde en 127.0.0.1:11434. Abre Ollama y vuelve a probar."
}

$listener = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue
Check-Result "Puerto 5000" (-not $listener) "Debe estar libre antes de iniciar WA-Bridge AI."

Write-Host ""
if ($failed) {
    Write-Host "Diagnóstico terminado: hay elementos que revisar. No se cambió ninguna configuración." -ForegroundColor Yellow
} else {
    Write-Host "Diagnóstico terminado: comprobaciones principales correctas." -ForegroundColor Green
}
