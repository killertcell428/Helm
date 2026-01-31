# Google Cloud CLI Setup Fix Script
# Run this script as Administrator

Write-Host "=== Google Cloud CLI Setup Fix ===" -ForegroundColor Green
Write-Host ""

# Get Python path
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) {
    Write-Host "Error: Python not found" -ForegroundColor Red
    Write-Host "Please install Python or add it to PATH" -ForegroundColor Yellow
    exit 1
}

Write-Host "Python path: $pythonPath" -ForegroundColor Yellow
Write-Host ""

# Set CLOUDSDK_PYTHON environment variable
Write-Host "[1/3] Setting CLOUDSDK_PYTHON environment variable..." -ForegroundColor Green
try {
    [System.Environment]::SetEnvironmentVariable("CLOUDSDK_PYTHON", $pythonPath, "User")
    Write-Host "OK: Set in user environment variables" -ForegroundColor Green
} catch {
    Write-Host "Warning: Failed to set user environment variable: $_" -ForegroundColor Yellow
    Write-Host "Please run as Administrator" -ForegroundColor Yellow
}

# Set for current session
$env:CLOUDSDK_PYTHON = $pythonPath
Write-Host "OK: Set for current session" -ForegroundColor Green
Write-Host ""

# Create Google Cloud SDK temp directory
$gcloudPath = "C:\Program Files (x86)\Google\Cloud SDK"
if (Test-Path $gcloudPath) {
    Write-Host "[2/3] Creating Google Cloud SDK temp directory..." -ForegroundColor Green
    $tmpDir = Join-Path $gcloudPath "tmp"
    try {
        if (-not (Test-Path $tmpDir)) {
            New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
            Write-Host "OK: Created temp directory: $tmpDir" -ForegroundColor Green
        } else {
            Write-Host "OK: Temp directory already exists: $tmpDir" -ForegroundColor Green
        }
    } catch {
        Write-Host "Warning: Failed to create temp directory: $_" -ForegroundColor Yellow
        Write-Host "Please run as Administrator" -ForegroundColor Yellow
    }
} else {
    Write-Host "[2/3] Google Cloud SDK path not found: $gcloudPath" -ForegroundColor Yellow
    Write-Host "It may be installed in a different location" -ForegroundColor Yellow
}
Write-Host ""

# Verify Google Cloud CLI
Write-Host "[3/3] Verifying Google Cloud CLI..." -ForegroundColor Green
try {
    $gcloudVersion = gcloud version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK: Google Cloud CLI is working correctly" -ForegroundColor Green
        Write-Host ""
        Write-Host $gcloudVersion
    } else {
        Write-Host "Warning: Google Cloud CLI has issues" -ForegroundColor Yellow
        Write-Host $gcloudVersion
    }
} catch {
    Write-Host "Error: Google Cloud CLI not found" -ForegroundColor Red
    Write-Host "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Open a new terminal and verify with:" -ForegroundColor Yellow
Write-Host "  gcloud version" -ForegroundColor Cyan
Write-Host ""
Write-Host "If problems persist, run this script as Administrator" -ForegroundColor Yellow