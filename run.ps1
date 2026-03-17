<#
.SYNOPSIS
  One-command runner for Trading-Software on Windows.

.PARAMETER Port
  Port to listen on (default: 8000).

.PARAMETER BindHost
  Host/IP to bind to (default: 127.0.0.1).

.PARAMETER NoReload
  Pass this switch to disable Uvicorn's --reload flag.

.EXAMPLE
  .\run.ps1
  .\run.ps1 -Port 8001
  .\run.ps1 -BindHost 0.0.0.0 -NoReload
#>
param(
    [int]$Port     = 8000,
    [string]$BindHost  = "127.0.0.1",
    [switch]$NoReload
)

$ErrorActionPreference = "Stop"

function Info($msg) { Write-Host "[run] $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "[run] $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "[run] ERROR: $msg" -ForegroundColor Red; exit 1 }

# ── 1. Validate repo root ──────────────────────────────────────────────────────
if (-not (Test-Path ".\requirements.txt")) {
    Fail "requirements.txt not found.`nPlease run this script from the repository root folder."
}

# ── 2. Locate Python ──────────────────────────────────────────────────────────
$python = $null
foreach ($candidate in @("python", "py")) {
    try {
        $resolved = (Get-Command $candidate -ErrorAction Stop).Source
        # Quick sanity-check: make sure it actually runs
        $ver = & $resolved --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $python = $resolved
            break
        }
    } catch {
        # not found, try next
    }
}

if (-not $python) {
    Fail "Python not found.`nInstall Python 3.10+ from https://www.python.org/downloads/ and make sure it is on PATH (or use the Windows 'py' launcher)."
}

Info "Using Python: $python"

# ── 3. Create virtual environment if absent ────────────────────────────────────
$venvPython = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Info "Creating virtual environment in .venv ..."
    & $python -m venv .venv
    if ($LASTEXITCODE -ne 0) { Fail "Failed to create virtual environment." }
} else {
    Info "Virtual environment already exists."
}

# ── 4. Upgrade pip ────────────────────────────────────────────────────────────
Info "Upgrading pip ..."
& $venvPython -m pip install --upgrade pip | Out-Host
if ($LASTEXITCODE -ne 0) { Fail "pip upgrade failed." }

# ── 5. Install dependencies ───────────────────────────────────────────────────
Info "Installing dependencies from requirements.txt ..."
& $venvPython -m pip install -r requirements.txt | Out-Host
if ($LASTEXITCODE -ne 0) { Fail "Dependency installation failed." }

# ── 6. Create .env if missing ─────────────────────────────────────────────────
if (-not (Test-Path ".\.env")) {
    if (Test-Path ".\.env.example") {
        Info "Creating .env from .env.example ..."
        Copy-Item ".\.env.example" ".\.env"
        Warn "Remember to open .env and fill in your API keys."
    } else {
        Warn ".env.example not found; skipping .env creation. Create .env manually if required."
    }
} else {
    Info ".env already exists — skipping creation."
}

# ── 7. Start server ───────────────────────────────────────────────────────────
$uvicornArgs = @("app.main:app", "--host", $BindHost, "--port", $Port)
if (-not $NoReload) {
    $uvicornArgs += "--reload"
}

Info "Starting server on http://${BindHost}:${Port}  (press Ctrl+C to stop) ..."
& $venvPython -m uvicorn @uvicornArgs
