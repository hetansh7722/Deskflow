<#
.SYNOPSIS
  One-command setup for DeskFlow: venv, dependencies, .env, tests.

.EXAMPLE
  .\setup.ps1
#>
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "[1/4] Creating virtual environment..." -ForegroundColor Cyan
if (-not (Test-Path "venv")) { python -m venv venv }
$py = ".\venv\Scripts\python.exe"

Write-Host "[2/4] Installing dependencies..." -ForegroundColor Cyan
& $py -m pip install --upgrade pip --quiet
& $py -m pip install -r requirements.txt -r requirements-dev.txt --quiet

Write-Host "[3/4] Preparing .env..." -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created .env from .env.example - add your GROQ_API_KEY" -ForegroundColor Yellow
}
else {
    Write-Host "  .env already exists - left untouched" -ForegroundColor DarkGray
}

Write-Host "[4/4] Running tests..." -ForegroundColor Cyan
& $py -m pytest tests -q | Out-Host

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "  Start server : .\venv\Scripts\python.exe main.py"
Write-Host "  Open         : http://localhost:8000  (login: see README demo credentials)"
Write-Host "  Admin view   : http://localhost:8000/static/admin.html"
