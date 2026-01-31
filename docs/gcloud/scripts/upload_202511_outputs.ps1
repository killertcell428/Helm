# 202511_outputsをGoogle Cloud Storageにアップロードするスクリプト
# 文字化け対策: UTF-8エンコーディングと、フォントを「ＭＳ ゴシック」に指定し日本語が確実に読めるように

param(
    [string]$BucketName = ""
)

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    # コマンドプロンプトのコードページをUTF-8に変更（可能な場合）
    $null = chcp 65001 2>$null
    # コンソールで日本語が正しく表示されるフォントを指定（MS ゴシックは日本語Windowsの標準）
    $host.UI.RawUI.Font = New-Object System.Management.Automation.Host.FontInfo("MS Gothic", 12)
} catch {
    # エンコーディングまたはフォント設定に失敗しても続行
}

$ErrorActionPreference = "Stop"

Write-Host "=== 202511_outputs Cloud Storage アップロードスクリプト ===" -ForegroundColor Green
Write-Host ""

# バケット名の取得
$GCS_BUCKET_NAME = ""
if ($BucketName) {
    $GCS_BUCKET_NAME = $BucketName
    Write-Host "バケット名（引数から）: $GCS_BUCKET_NAME" -ForegroundColor Yellow
} elseif ($env:GCS_BUCKET_NAME) {
    $GCS_BUCKET_NAME = $env:GCS_BUCKET_NAME
    Write-Host "バケット名（環境変数から）: $GCS_BUCKET_NAME" -ForegroundColor Yellow
} else {
    Write-Host "エラー: Cloud Storageバケット名が指定されていません" -ForegroundColor Red
    Write-Host ""
    Write-Host "使用方法:" -ForegroundColor Yellow
    Write-Host "  1. 環境変数を設定:" -ForegroundColor White
    Write-Host '     $env:GCS_BUCKET_NAME = "your-bucket-name"' -ForegroundColor Cyan
    Write-Host "     .\gcloud\scripts\upload_202511_outputs.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. 引数で指定:" -ForegroundColor White
    Write-Host '     .\gcloud\scripts\upload_202511_outputs.ps1 -BucketName "your-bucket-name"' -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

Write-Host ""

# バケットの存在確認
Write-Host "バケットの存在を確認中..." -ForegroundColor Yellow
$bucketExists = $false
try {
    $null = gsutil ls "gs://$GCS_BUCKET_NAME" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $bucketExists = $true
        Write-Host "✓ バケットが存在します: gs://$GCS_BUCKET_NAME" -ForegroundColor Green
    }
} catch {
    # バケットが存在しない場合は続行
}

if (-not $bucketExists) {
    Write-Host ""
    Write-Host "警告: バケットが存在しません: gs://$GCS_BUCKET_NAME" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "バケットを作成するには、以下のコマンドを実行してください:" -ForegroundColor Yellow
    Write-Host ""
    $PROJECT_ID = gcloud config get-value project 2>$null
    if ($PROJECT_ID) {
        Write-Host "  # プロジェクトID: $PROJECT_ID" -ForegroundColor Gray
        Write-Host "  gsutil mb -p $PROJECT_ID -l asia-northeast1 gs://$GCS_BUCKET_NAME" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  # Cloud Runサービスアカウントに権限を付与" -ForegroundColor Gray
        $PROJECT_NUMBER = gcloud projects describe $PROJECT_ID --format="value(projectNumber)" 2>$null
        if ($PROJECT_NUMBER) {
            Write-Host "  " -NoNewline -ForegroundColor Cyan
            Write-Host '$env:PROJECT_NUMBER = "' -NoNewline -ForegroundColor Cyan
            Write-Host "$PROJECT_NUMBER" -NoNewline -ForegroundColor Cyan
            Write-Host '"' -ForegroundColor Cyan
            Write-Host "  gcloud projects add-iam-policy-binding $PROJECT_ID" -ForegroundColor Cyan
            Write-Host '    --member="serviceAccount:$env:PROJECT_NUMBER-compute@developer.gserviceaccount.com"' -ForegroundColor Cyan
            Write-Host '    --role="roles/storage.objectAdmin"' -ForegroundColor Cyan
        }
    } else {
        Write-Host "  gsutil mb -p YOUR_PROJECT_ID -l asia-northeast1 gs://$GCS_BUCKET_NAME" -ForegroundColor Cyan
    }
    Write-Host ""
    Write-Host "詳細は gcloud/docs/DEPLOY_GCLOUD.md を参照してください" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""

# ソースディレクトリの確認
$SOURCE_DIR = "back\outputs"
if (-not (Test-Path $SOURCE_DIR)) {
    Write-Host "エラー: ソースディレクトリが見つかりません: $SOURCE_DIR" -ForegroundColor Red
    Write-Host ""
    Write-Host "確認してください:" -ForegroundColor Yellow
    Write-Host "  - back/outputs/ ディレクトリが存在するか" -ForegroundColor White
    Write-Host "  - スクリプトをプロジェクトルートから実行しているか" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "ソースディレクトリ: $SOURCE_DIR" -ForegroundColor Yellow
Write-Host "アップロード先: gs://$GCS_BUCKET_NAME/outputs/" -ForegroundColor Yellow
Write-Host ""

# アップロード前の確認
$fileCount = (Get-ChildItem -Path $SOURCE_DIR -Recurse -File | Measure-Object).Count
Write-Host "アップロード対象ファイル数: $fileCount" -ForegroundColor Cyan
Write-Host ""
Write-Host "注意: 既存のCloud Storageのoutputsデータは上書きされます" -ForegroundColor Yellow
Write-Host ""

$confirmation = Read-Host "アップロードを続行しますか？ (y/N)"
if ($confirmation -ne "y" -and $confirmation -ne "Y") {
    Write-Host "アップロードをキャンセルしました" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "アップロードを開始します..." -ForegroundColor Green
Write-Host "（これには数分かかる場合があります）" -ForegroundColor Yellow
Write-Host ""

# gsutil rsyncを使用してローカルのoutputsをCloud Storageに同期
# -r: 再帰的に同期
# -m: 並列処理で高速化
# 既存ファイルも含めてすべてアップロード（過去の実行結果も保存）
$GCS_DEST = "gs://$GCS_BUCKET_NAME/outputs/"
gsutil -m rsync -r "$SOURCE_DIR" "$GCS_DEST"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== アップロードが完了しました！ ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "アップロード先: $GCS_DEST" -ForegroundColor Cyan
    Write-Host "ファイル数: $fileCount" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "デプロイ先環境で実行結果を確認できます" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "エラー: アップロードに失敗しました" -ForegroundColor Red
    Write-Host ""
    Write-Host "確認事項:" -ForegroundColor Yellow
    Write-Host "  - Google Cloud CLIがインストールされているか" -ForegroundColor White
    Write-Host "  - gcloud auth login で認証しているか" -ForegroundColor White
    Write-Host "  - バケット名が正しいか" -ForegroundColor White
    Write-Host "  - バケットへの書き込み権限があるか" -ForegroundColor White
    Write-Host ""
    exit 1
}
