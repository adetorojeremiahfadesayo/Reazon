param(
  [int]$ApiPort = 8000,
  [int]$WebPort = 5173
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$WebDir = Join-Path $Root "web"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$ApiUrl = "http://127.0.0.1:$ApiPort"
$StartedApiProcess = $null

if (-not (Test-Path $Python)) {
  Write-Host "Creating Python virtual environment"
  Push-Location $Root
  try {
    python -m venv .venv
  } finally {
    Pop-Location
  }
}

if (-not (Test-Path $Python)) {
  throw "Virtualenv Python was not found at $Python. Install Python 3, then rerun this launcher."
}

$depsReady = & $Python -c "import fastapi, uvicorn" 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Installing Python demo dependencies"
  & $Python -m pip install -r (Join-Path $Root "requirements.txt")
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  throw "npm was not found. Install Node.js LTS, then rerun this launcher."
}

if (-not (Test-Path (Join-Path $WebDir "node_modules"))) {
  Write-Host "Installing web demo dependencies"
  Push-Location $WebDir
  try {
    npm install
  } finally {
    Pop-Location
  }
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
  $StartedApiProcess = Start-Process -FilePath $Python `
    -ArgumentList @("-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "$ApiPort") `
    -WorkingDirectory $Root `
    -WindowStyle Hidden `
    -PassThru

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

Push-Location $WebDir
try {
  $env:VITE_API_PORT = "$ApiPort"
  $env:REAZON_DISABLE_AUTO_API = "true"
  Write-Host "Starting Reazon web app on http://127.0.0.1:$WebPort"
  npm run dev -- --port $WebPort
} finally {
  Pop-Location
  if ($StartedApiProcess -and -not $StartedApiProcess.HasExited) {
    Write-Host "Stopping Reazon API process $($StartedApiProcess.Id)"
    Stop-Process -Id $StartedApiProcess.Id
  }
}
