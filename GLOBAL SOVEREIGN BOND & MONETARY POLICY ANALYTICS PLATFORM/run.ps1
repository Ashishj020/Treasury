# POLICY → YIELDS local runners (Windows PowerShell)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Start-Backend {
  Set-Location "$root\backend"
  if (-not (Test-Path .venv)) { python -m venv .venv }
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
}

function Start-Frontend {
  Set-Location "$root\frontend"
  if (-not (Test-Path node_modules)) { npm install }
  # Folder name contains "&" which breaks `npm run dev` on Windows cmd.
  node .\node_modules\vite\bin\vite.js --host 127.0.0.1 --port 5173
}

if ($args[0] -eq "api") { Start-Backend }
elseif ($args[0] -eq "web") { Start-Frontend }
else {
  Write-Host "Usage:`n  .\run.ps1 api     # FastAPI on :8000`n  .\run.ps1 web     # Vite on :5173"
}
