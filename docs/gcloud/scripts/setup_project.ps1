# REACHA Project Setup Script
# This script creates a new project and sets it up for deployment

Write-Host "=== REACHA Project Setup ===" -ForegroundColor Green
Write-Host ""

# Generate a unique project ID
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$projectId = "reacha-app-$timestamp"

Write-Host "Creating new project: $projectId" -ForegroundColor Yellow
Write-Host ""

# Create the project
Write-Host "[1/3] Creating project..." -ForegroundColor Green
try {
    gcloud projects create $projectId --name="REACHA Application"
    Write-Host "OK: Project created successfully" -ForegroundColor Green
} catch {
    Write-Host "Error: Failed to create project" -ForegroundColor Red
    Write-Host "You may need to create it manually or use an existing project" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Existing projects:" -ForegroundColor Cyan
    gcloud projects list
    Write-Host ""
    Write-Host "To use an existing project, run:" -ForegroundColor Yellow
    Write-Host "  gcloud config set project PROJECT_ID" -ForegroundColor Cyan
    exit 1
}

Write-Host ""

# Set the project
Write-Host "[2/3] Setting project..." -ForegroundColor Green
gcloud config set project $projectId
Write-Host "OK: Project set to $projectId" -ForegroundColor Green
Write-Host ""

# Enable required APIs
Write-Host "[3/3] Enabling required APIs..." -ForegroundColor Green
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
Write-Host "OK: Required APIs enabled" -ForegroundColor Green
Write-Host ""

Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Project ID: $projectId" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Build frontend: cd flont && npm run build && cd .." -ForegroundColor White
Write-Host "2. Deploy: .\deploy.ps1" -ForegroundColor White
Write-Host ""
