# Case1 デモ デプロイ前検証スクリプト
# 実行: .\Dev\scripts\verify_case1_deploy.ps1

$ErrorActionPreference = "Stop"
$backendUrl = "http://localhost:8000"
$frontendUrl = "http://localhost:3000"

Write-Host "`n=== Case1 デプロイ前検証 ===" -ForegroundColor Cyan

# 1. バックエンドヘルスチェック
Write-Host "`n[1/4] バックエンドヘルスチェック..." -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "$backendUrl/" -UseBasicParsing -TimeoutSec 5
    if ($r.StatusCode -eq 200) {
        Write-Host "  OK: バックエンドは起動しています" -ForegroundColor Green
    } else {
        Write-Host "  NG: ステータス $($r.StatusCode)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  NG: バックエンドに接続できません。uvicorn main:app --reload --host 0.0.0.0 --port 8000 で起動してください" -ForegroundColor Red
    exit 1
}

# 2. フロントエンドヘルスチェック
Write-Host "`n[2/4] フロントエンドヘルスチェック..." -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "$frontendUrl/" -UseBasicParsing -TimeoutSec 5
    if ($r.StatusCode -eq 200) {
        Write-Host "  OK: フロントエンドは起動しています" -ForegroundColor Green
    } else {
        Write-Host "  NG: ステータス $($r.StatusCode)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  NG: フロントエンドに接続できません。pnpm dev で起動してください" -ForegroundColor Red
    exit 1
}

# 3. Case1ページの存在確認
Write-Host "`n[3/4] Case1ページ確認..." -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "$frontendUrl/demo/case1" -UseBasicParsing -TimeoutSec 10
    if ($r.StatusCode -eq 200 -and $r.Content -match "Case 1") {
        Write-Host "  OK: /demo/case1 が正常に応答しています" -ForegroundColor Green
    } else {
        Write-Host "  NG: Case1ページの応答が不正" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  NG: Case1ページにアクセスできません" -ForegroundColor Red
    exit 1
}

# 4. Case1 API統合テスト
Write-Host "`n[4/4] Case1 API統合テスト（約1分）..." -ForegroundColor Yellow
$backendDir = Join-Path (Split-Path $PSScriptRoot -Parent) "backend"
Push-Location $backendDir
try {
    $result = python -m pytest tests/integration/test_case1_demo_flow.py -v --tb=short 2>&1
    Pop-Location
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK: Case1フロー統合テスト成功" -ForegroundColor Green
    } else {
        Write-Host "  NG: 統合テスト失敗" -ForegroundColor Red
        Write-Host $result
        exit 1
    }
} catch {
    Pop-Location
    Write-Host "  NG: テスト実行エラー: $_" -ForegroundColor Red
    exit 1
}

Write-Host ''
Write-Host '=== All checks passed: Ready for deployment ===' -ForegroundColor Green
Write-Host 'Open http://localhost:3000/demo/case1 in browser' -ForegroundColor Cyan
