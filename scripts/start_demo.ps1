param(
  [int]$ApiPort = 8000,
  [int]$WebPort = 5173
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
  throw "Virtualenv Python was not found at $Python. Run: python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt"
}

Write-Host "Starting Reazon API on http://127.0.0.1:$ApiPort"
Start-Process -FilePath $Python `
  -ArgumentList @("-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "$ApiPort") `
  -WorkingDirectory $Root `
  -WindowStyle Hidden

Push-Location (Join-Path $Root "web")
try {
  Write-Host "Starting Reazon web app on http://127.0.0.1:$WebPort"
  npm run dev -- --port $WebPort
} finally {
  Pop-Location
}
