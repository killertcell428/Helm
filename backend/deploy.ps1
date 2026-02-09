# Helm Backend API + Frontend Deployment Script
# バックエンド: Google Cloud Run / フロント: Vercel
# オプションで -BackendOnly を付けるとフロントデプロイをスキップします

param(
    [switch]$BackendOnly  # 指定時は Cloud Run のみ（Vercel はスキップ）
)

Write-Host "=== Helm Deployment (Backend + Frontend) ===" -ForegroundColor Green
if ($BackendOnly) {
    Write-Host "Mode: Backend only (Cloud Run)" -ForegroundColor Yellow
} else {
    Write-Host "Mode: Full (Cloud Run + Vercel)" -ForegroundColor Cyan
}
Write-Host ""

# エラー時に停止
$ErrorActionPreference = "Stop"

# スクリプトのディレクトリに移動（スクリプトがどこから実行されても正しいディレクトリで動作）
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# プロジェクトIDの設定（既存プロジェクトを使用）
$PROJECT_ID = "helm-project-484105"
$SERVICE_NAME = "helm-api"
$REGION = "asia-northeast1"
# 変数展開を確実にするため、文字列連結を使用
$IMAGE_NAME = "gcr.io/" + $PROJECT_ID + "/" + $SERVICE_NAME

# プロジェクトの確認
Write-Host "[1/5] Checking project configuration..." -ForegroundColor Green
try {
    $currentProject = gcloud config get-value project 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: gcloud is not installed or not configured" -ForegroundColor Red
        Write-Host "Please install Google Cloud SDK and run 'gcloud auth login'" -ForegroundColor Yellow
        exit 1
    }
    
    if ($currentProject -ne $PROJECT_ID) {
        Write-Host "Setting project to $PROJECT_ID..." -ForegroundColor Yellow
        gcloud config set project $PROJECT_ID
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: Failed to set project" -ForegroundColor Red
            exit 1
        }
    }
    Write-Host "OK: Project is set to $PROJECT_ID" -ForegroundColor Green
} catch {
    Write-Host "Error: Failed to check project configuration" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""

# Dockerの確認
Write-Host "[2/5] Checking Docker..." -ForegroundColor Green
try {
    docker version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Docker is not running or not installed" -ForegroundColor Red
        Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "OK: Docker is available" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker is not available" -ForegroundColor Red
    Write-Host "Please install Docker Desktop and start it" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Docker認証の設定
Write-Host "[3/5] Configuring Docker authentication..." -ForegroundColor Green
try {
    gcloud auth configure-docker gcr.io --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to configure Docker authentication" -ForegroundColor Red
        exit 1
    }
    Write-Host "OK: Docker authentication configured" -ForegroundColor Green
} catch {
    Write-Host "Error: Failed to configure Docker authentication" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""

# Dockerイメージのビルド
Write-Host "[4/5] Building Docker image..." -ForegroundColor Green
# 変数の値を確認（デバッグ用）
Write-Host "PROJECT_ID: $PROJECT_ID" -ForegroundColor Gray
Write-Host "SERVICE_NAME: $SERVICE_NAME" -ForegroundColor Gray
Write-Host "IMAGE_NAME: $IMAGE_NAME" -ForegroundColor Gray

# 完全なイメージ名を構築（文字列連結で確実に）
$fullImageName = $IMAGE_NAME + ":latest"
Write-Host "Image: $fullImageName" -ForegroundColor Cyan
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Gray

try {
    # 現在のディレクトリを確認
    if (-not (Test-Path "Dockerfile")) {
        Write-Host "Error: Dockerfile not found in current directory" -ForegroundColor Red
        Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
        exit 1
    }
    
    # Dockerビルドコマンドを実行
    # 直接コマンドを実行（配列スプラッティングで問題が発生する可能性があるため）
    Write-Host "Executing: docker build -t `"$fullImageName`" ." -ForegroundColor Gray
    
    # docker buildコマンドを直接実行
    docker build -t $fullImageName .
    $buildExitCode = $LASTEXITCODE
    
    if ($buildExitCode -ne 0) {
        Write-Host "Error: Docker build failed (exit code: $buildExitCode)" -ForegroundColor Red
        exit 1
    }
    Write-Host "OK: Docker image built successfully" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker build failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Exception type: $($_.Exception.GetType().FullName)" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Container Registryへのプッシュ
Write-Host "[5/5] Pushing image to Container Registry..." -ForegroundColor Green
try {
    # 完全なイメージ名を構築
    $fullImageName = $IMAGE_NAME + ":latest"
    Write-Host "Pushing: $fullImageName" -ForegroundColor Cyan
    
    # Dockerプッシュコマンドを直接実行
    Write-Host "Executing: docker push `"$fullImageName`"" -ForegroundColor Gray
    docker push $fullImageName
    $pushExitCode = $LASTEXITCODE
    
    if ($pushExitCode -ne 0) {
        Write-Host "Error: Failed to push image to Container Registry (exit code: $pushExitCode)" -ForegroundColor Red
        exit 1
    }
    Write-Host "OK: Image pushed successfully" -ForegroundColor Green
} catch {
    Write-Host "Error: Failed to push image" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""

# Cloud Runへのデプロイ
Write-Host "[6/6] Deploying to Cloud Run..." -ForegroundColor Green
Write-Host "Service: $SERVICE_NAME" -ForegroundColor Cyan
Write-Host "Region: $REGION" -ForegroundColor Cyan
Write-Host ""

try {
    # 完全なイメージ名を構築
    $fullImageName = $IMAGE_NAME + ":latest"
    Write-Host "Deploying image: $fullImageName" -ForegroundColor Gray
    
    # gcloud run deployコマンドを直接実行
    # PowerShellの行継続を使わず、1行で構築して実行
    # 注意: --set-env-varsは既存の環境変数をすべて置き換えるため、--update-env-varsを使用しない
    # 環境変数はデプロイ後に別途設定する必要がある
    $deployCommand = "gcloud run deploy $SERVICE_NAME --image `"$fullImageName`" --region $REGION --platform managed --allow-unauthenticated --memory 2Gi --cpu 2 --timeout 3600 --max-instances 10 --update-env-vars OUTPUT_DIR=/tmp/outputs"
    
    Write-Host "Executing: $deployCommand" -ForegroundColor Gray
    Invoke-Expression $deployCommand
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Deployment failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "=== Backend (Cloud Run) Deployment Complete ===" -ForegroundColor Green
    Write-Host ""
    
    # サービスのURLを取得
    $serviceUrl = gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)' 2>&1
    if ($LASTEXITCODE -eq 0 -and $serviceUrl) {
        Write-Host "Service URL: $serviceUrl" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Next steps (backend):" -ForegroundColor Yellow
        Write-Host "1. Set environment variables (see MANUAL_SETUP_GUIDE.md)" -ForegroundColor White
        Write-Host "2. Test the API: $serviceUrl/docs" -ForegroundColor White
        Write-Host "3. Check logs: gcloud run services logs read $SERVICE_NAME --region $REGION" -ForegroundColor White
    } else {
        Write-Host "Deployment completed, but failed to get service URL" -ForegroundColor Yellow
        Write-Host "Check the service status in Google Cloud Console" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "Error: Deployment failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check if billing is enabled: gcloud billing accounts list" -ForegroundColor White
    Write-Host "2. Check if required APIs are enabled" -ForegroundColor White
    Write-Host "3. Check logs: gcloud run services logs read $SERVICE_NAME --region $REGION --limit 50" -ForegroundColor White
    exit 1
}

# --- フロントエンド (Vercel) デプロイ（オプション） ---
if (-not $BackendOnly) {
    Write-Host ""
    Write-Host "[7/7] Deploying frontend to Vercel..." -ForegroundColor Green
    $frontendPath = Join-Path (Split-Path $scriptPath -Parent) "app\v0-helm-demo"
    if (-not (Test-Path $frontendPath)) {
        Write-Host "Warning: Frontend path not found: $frontendPath" -ForegroundColor Yellow
        Write-Host "Skipping Vercel deploy. Run 'vercel --prod' from Dev/app/v0-helm-demo manually if needed." -ForegroundColor Yellow
    } else {
        $vercelCmd = Get-Command vercel -ErrorAction SilentlyContinue
        if (-not $vercelCmd) {
            Write-Host "Warning: Vercel CLI not found (npm i -g vercel or pnpm add -g vercel)." -ForegroundColor Yellow
            Write-Host "Skipping frontend deploy. Push to main for auto-deploy or run 'vercel --prod' from Dev/app/v0-helm-demo." -ForegroundColor Yellow
        } else {
            try {
                Push-Location $frontendPath
                Write-Host "Working directory: $(Get-Location)" -ForegroundColor Gray
                Write-Host "Executing: vercel --prod" -ForegroundColor Gray
                vercel --prod
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "Error: Vercel deploy failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
                    Write-Host "Ensure you are logged in: vercel login" -ForegroundColor Yellow
                    Pop-Location
                    exit 1
                }
                Write-Host "OK: Frontend deployed to Vercel (production)" -ForegroundColor Green
                Pop-Location
            } catch {
                Write-Host "Error: Vercel deploy failed" -ForegroundColor Red
                Write-Host $_.Exception.Message -ForegroundColor Red
                try { Pop-Location } catch { }
                exit 1
            }
        }
    }
    Write-Host ""
    Write-Host "=== Full Deployment Complete (Backend + Frontend) ===" -ForegroundColor Green
}

Write-Host ""
