$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

$script:failed = $false
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
    if ($versionOk) {
        & py -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
        $versionOk = $LASTEXITCODE -eq 0
    }
    Check-Result "Python 3.10+" $versionOk "$versionText"
} else {
    Check-Result "Python 3.10+" $false "No se encontró el lanzador 'py'."
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$venvExists = Test-Path $venvPython
Check-Result "Entorno virtual" $venvExists "Se busca .venv\Scripts\python.exe."
if ($venvExists) {
    & $venvPython -c "import flask, dotenv"
    Check-Result "Dependencias Python" ($LASTEXITCODE -eq 0) "Se comprueban Flask y python-dotenv."
} else {
    Check-Result "Dependencias Python" $false "Instala primero con .\setup_windows.ps1."
}

$envFile = Join-Path $PSScriptRoot ".env"
$envExists = Test-Path $envFile
Check-Result "Configuración .env" $envExists "Se busca .env; sus valores nunca se muestran."

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
    $modelList = & ollama list 2>&1 | Out-String
    $ollamaOk = $LASTEXITCODE -eq 0
    Check-Result "Ollama CLI" $ollamaOk "Se pudo consultar ollama list."
    $modelOk = $ollamaOk -and ($modelList -match "qwen2\.5:1\.5b")
    Check-Result "Modelo Qwen 2.5 1.5B" $modelOk "Se busca el modelo existente; no se descarga automáticamente."
} else {
    Check-Result "Ollama CLI" $false "No se encontró ollama en PATH."
    Check-Result "Modelo Qwen 2.5 1.5B" $false "No se pudo comprobar el modelo."
}

try {
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3
    Check-Result "Servicio Ollama" $true "Responde en 127.0.0.1:11434."
} catch {
    Check-Result "Servicio Ollama" $false "No responde en 127.0.0.1:11434. Abre Ollama y vuelve a probar."
}

$portToCheck = 5000
$portRaw = $env:PORT
if (-not $portRaw -and $envExists) {
    $portLine = Get-Content $envFile | Where-Object { $_ -match '^\s*PORT\s*=' } | Select-Object -First 1
    if ($portLine) {
        $parts = $portLine -split '=', 2
        if ($parts.Count -eq 2) { $portRaw = $parts[1].Trim() }
    }
}
if ($portRaw) {
    $parsedPort = 0
    if ([int]::TryParse($portRaw, [ref]$parsedPort)) {
        $portToCheck = $parsedPort
    } else {
        $portToCheck = 0
    }
}

if ($portToCheck -lt 1 -or $portToCheck -gt 65535) {
    Check-Result "Puerto configurado" $false "PORT debe ser un entero entre 1 y 65535."
} else {
    $tcpCommand = Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue
    if ($tcpCommand) {
        $listeners = @(Get-NetTCPConnection -LocalPort $portToCheck -State Listen -ErrorAction SilentlyContinue)
        if ($listeners.Count -eq 0) {
            Check-Result "Puerto $portToCheck libre" $true "No hay un proceso escuchando."
        } else {
            $owners = ($listeners | Select-Object -ExpandProperty OwningProcess -Unique) -join ", "
            Check-Result "Puerto $portToCheck libre" $false "Está ocupado. PID detectado: $owners. No se cerró ningún proceso."
        }
    } else {
        $netstat = netstat -ano -p tcp 2>$null | Out-String
        $portPattern = ":\s*$portToCheck\s"
        $portInUse = $netstat -match "(?m)^\s*TCP\s+\S+$portPattern\S+\s+LISTENING\s+"
        Check-Result "Puerto $portToCheck libre" (-not $portInUse) "Comprobación mediante netstat."
    }
}

Write-Host ""
if ($script:failed) {
    Write-Host "Diagnóstico terminado: hay requisitos pendientes. Revisa las líneas [FALTA]." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "Diagnóstico terminado: todas las comprobaciones pasaron." -ForegroundColor Green
    exit 0
}
