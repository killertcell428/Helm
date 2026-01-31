# Cloud Run環境変数設定スクリプト
# CORS_ORIGINSに特殊文字が含まれるため、環境変数ファイルを使用

Write-Host "=== Cloud Run環境変数設定 ===" -ForegroundColor Green
Write-Host ""

# 環境変数ファイルを作成
$envVarsFile = "env-vars.yaml"
$envVarsContent = @"
GOOGLE_API_KEY: AIzaSyCnf9uZEpMZSMK8fxRzIfhER1LI6ABujPQ
USE_LLM: 'true'
GOOGLE_CLOUD_PROJECT_ID: helm-project-484105
CORS_ORIGINS: 'http://localhost:3000,https://*.vercel.app'
OUTPUT_DIR: /tmp/outputs
"@

Write-Host "環境変数ファイルを作成中..." -ForegroundColor Cyan
$envVarsContent | Out-File -FilePath $envVarsFile -Encoding utf8

Write-Host "環境変数を設定中..." -ForegroundColor Cyan
gcloud run services update helm-api `
  --region asia-northeast1 `
  --env-vars-file $envVarsFile

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 環境変数の設定が完了しました！" -ForegroundColor Green
    Write-Host ""
    Write-Host "設定された環境変数:" -ForegroundColor Yellow
    gcloud run services describe helm-api --region asia-northeast1 --format="value(spec.template.spec.containers[0].env)"
} else {
    Write-Host ""
    Write-Host "❌ 環境変数の設定に失敗しました" -ForegroundColor Red
    exit 1
}

# 一時ファイルを削除
Remove-Item $envVarsFile -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== 完了 ===" -ForegroundColor Green
