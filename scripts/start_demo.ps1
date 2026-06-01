param(
  [int]$ApiPort = 8000,
  [int]$WebPort = 5173
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$ApiUrl = "http://127.0.0.1:$ApiPort"

if (-not (Test-Path $Python)) {
  throw "Virtualenv Python was not found at $Python. Run: python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt"
}

function Test-ApiHealthy {
  try {
    $response = Invoke-WebRequest -Uri "$ApiUrl/health" -UseBasicParsing -TimeoutSec 2
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
  } catch {
    return $false
  }
}

if (Test-ApiHealthy) {
  Write-Host "Reazon API is already running on $ApiUrl"
} else {
  Write-Host "Starting Reazon API on $ApiUrl"
  Start-Process -FilePath $Python `
    -ArgumentList @("-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "$ApiPort") `
    -WorkingDirectory $Root `
    -WindowStyle Hidden

  $deadline = (Get-Date).AddSeconds(15)
  while ((Get-Date) -lt $deadline) {
    if (Test-ApiHealthy) {
      break
    }
    Start-Sleep -Milliseconds 400
  }

  if (-not (Test-ApiHealthy)) {
    throw "Reazon API did not become healthy on $ApiUrl. Try running: $Python -m uvicorn api.main:app --host 127.0.0.1 --port $ApiPort"
  }
}

Push-Location (Join-Path $Root "web")
try {
  $env:VITE_API_PORT = "$ApiPort"
  Write-Host "Starting Reazon web app on http://127.0.0.1:$WebPort"
  npm run dev -- --port $WebPort
} finally {
  Pop-Location
}
