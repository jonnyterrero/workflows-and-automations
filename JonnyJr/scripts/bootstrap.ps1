# Requires: PowerShell 5+; Node 20+; Python 3.10+
$ErrorActionPreference = "Stop"

Write-Host "==> Bootstrapping JonnyJr (Windows)"

# Node / TS deps
if (Test-Path package.json) {
  Write-Host "Installing Node deps (workspace root + TS pkg)..."
  npm i -w @jonnyjr/ts 2>$null
  if ($LASTEXITCODE -ne 0) { npm i }
}

# Python venv + deps
Write-Host "Setting up Python venv..."
if (-Not (Test-Path .venv)) {
  python -m venv .venv
}
# Activate venv for this session
$venvActivate = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
  & $venvActivate
  python -m pip install --upgrade pip
  if (Test-Path ".\packages\py\requirements.txt") {
    pip install -r ".\packages\py\requirements.txt"
  }
} else {
  Write-Warning "Could not activate venv at $venvActivate"
}

# .env scaffold
if (-Not (Test-Path .env) -and (Test-Path .env.example)) {
  Copy-Item .env.example .env
  Write-Host "Created .env from .env.example (fill in OPENAI_API_KEY, PPLX_API_KEY)"
}

Write-Host "Done. Next:"
Write-Host "  npm -w @jonnyjr/ts run test"
Write-Host "  pytest -q"
