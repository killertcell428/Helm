# Refresh PATH for current PowerShell session
# Run this script to update PATH without restarting terminal

Write-Host "Refreshing PATH..." -ForegroundColor Green

# Get current PATH from system and user
$machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")

# Combine paths
$env:Path = "$machinePath;$userPath"

# Add Google Cloud SDK paths if they exist
$gcloudPaths = @(
    "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin",
    "C:\Users\$env:USERNAME\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin"
)

foreach ($gcloudPath in $gcloudPaths) {
    if (Test-Path $gcloudPath) {
        if ($env:Path -notlike "*$gcloudPath*") {
            $env:Path += ";$gcloudPath"
            Write-Host "Added to PATH: $gcloudPath" -ForegroundColor Yellow
        }
    }
}

Write-Host "PATH refreshed!" -ForegroundColor Green
Write-Host ""

# Verify gcloud
Write-Host "Verifying gcloud..." -ForegroundColor Cyan
try {
    $gcloudVersion = gcloud version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK: gcloud is now available" -ForegroundColor Green
        Write-Host $gcloudVersion
    } else {
        Write-Host "Warning: gcloud may not be working correctly" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error: gcloud still not found" -ForegroundColor Red
    Write-Host "You may need to restart the terminal" -ForegroundColor Yellow
}

Write-Host ""
