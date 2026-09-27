# Start LIQUIDITY → CONTROL locally (PowerShell)
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Start-Process python -ArgumentList "-m","uvicorn","app.main:app","--reload","--port","8765" -WorkingDirectory (Join-Path $root "backend")
Start-Process npm -ArgumentList "run","dev" -WorkingDirectory (Join-Path $root "frontend")
Write-Host "Backend http://127.0.0.1:8765"
Write-Host "Frontend http://localhost:5173 (or 5174 if 5173 is busy)"
