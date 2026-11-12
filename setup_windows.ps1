$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "== WA-Bridge AI: preparación de Windows ==" -ForegroundColor Cyan

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "No se encontró 'py'. Instala Python 3.10+ y vuelve a ejecutar."
}
py --version
py -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "Se requiere Python 3.10 o superior. Actualiza Python y vuelve a ejecutar."
}

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "Ollama detectado."
    $models = ollama list 2>$null | Out-String
    if ($models -match "qwen2.5:1.5b") {
        Write-Host "qwen2.5:1.5b ya está instalado; no se descargará." -ForegroundColor Green
    } else {
        Write-Warning "No se detectó qwen2.5:1.5b. No se descargará automáticamente para respetar el límite de almacenamiento."
    }
} else {
    Write-Warning "Ollama no está en PATH. La aplicación podrá usar su intérprete básico, pero Qwen requiere Ollama."
}

if (-not (Test-Path ".venv")) { py -m venv .venv }
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "No se pudo actualizar pip." }
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias." }

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ".env creado con la configuración local de Ollama."
} else {
    Write-Host ".env existente conservado; no se sobrescribió."
}
Write-Host "Preparación terminada. Ejecuta .\doctor_windows.ps1 y luego .\run_windows.ps1" -ForegroundColor Green
