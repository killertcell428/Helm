# REACHA Google Cloud Run デプロイ完全ガイド

このドキュメントは、REACHAアプリケーションをGoogle Cloud Runにデプロイするための完全な手順書です。初心者でも理解できるよう、実際に発生したエラーとその解決方法も含めています。

## 目次

1. [前提条件](#前提条件)
2. [Google Cloud CLI のセットアップ](#google-cloud-cli-のセットアップ)
3. [プロジェクトの作成と設定](#プロジェクトの作成と設定)
4. [Docker Desktop のインストール](#docker-desktop-のインストール)
5. [デプロイの実行](#デプロイの実行)
6. [環境変数の設定](#環境変数の設定)
7. [トラブルシューティング](#トラブルシューティング)
8. [更新デプロイ](#更新デプロイ)

---

## 前提条件

### 必要なソフトウェア

1. **Python 3.11以上**
   - インストール確認: `python --version`
   - ダウンロード: https://www.python.org/downloads/

2. **Node.js と npm**
   - フロントエンドビルド用
   - インストール確認: `node --version` と `npm --version`

3. **Google Cloud アカウント**
   - アカウント作成: https://cloud.google.com/
   - 課金アカウントの設定が必要

### 必要な知識

- 基本的なコマンドライン操作
- PowerShell（Windows）の基本操作

---

## Google Cloud CLI のセットアップ

### ステップ1: Google Cloud SDK のインストール

1. **インストーラーをダウンロード**
   - https://cloud.google.com/sdk/docs/install にアクセス
   - 「Windows 64-bit」のインストーラーをダウンロード

2. **インストール**
   - ダウンロードした `.exe` ファイルを実行
   - **管理者として実行**を推奨
   - インストール時に「Pythonの場所を自動検出」を選択

3. **インストール後の確認**
   - 新しいPowerShellを開く
   - 以下を実行：
     ```powershell
     gcloud version
     ```

### ステップ2: Python環境変数の設定

Google Cloud CLIがPythonを見つけられない場合、環境変数を設定します。

#### 方法1: 自動修正スクリプトを使用

```powershell
# プロジェクトディレクトリで実行
.\gcloud\scripts\fix_gcloud_setup.ps1
```

#### 方法2: 手動で設定

1. **Pythonのパスを確認**
   ```powershell
   where python
   ```

2. **環境変数を設定**
   - Windowsキー + R → `sysdm.cpl` → Enter
   - 「詳細設定」→「環境変数」
   - 「ユーザー環境変数」で「新規」
   - 変数名: `CLOUDSDK_PYTHON`
   - 変数値: `C:\Users\YourName\AppData\Local\Programs\Python\Python312\python.exe`（実際のパスに置き換え）

3. **PATHを更新（現在のセッション用）**
   ```powershell
   .\gcloud\scripts\refresh_path.ps1
   ```

### ステップ3: 認証と初期化

```powershell
# Google Cloudにログイン
gcloud auth login

# 初期化（プロジェクト選択）
gcloud init
```

---

## プロジェクトの作成と設定

### ステップ1: プロジェクトの作成

#### 方法1: 自動スクリプトを使用

```powershell
.\gcloud\scripts\setup_project.ps1
```

このスクリプトは以下を自動実行します：
- 新しいプロジェクトの作成
- プロジェクトの設定
- 必要なAPIの有効化

#### 方法2: 手動で作成

```powershell
# プロジェクトを作成
gcloud projects create reacha-app-YYYYMMDDHHMMSS --name="REACHA Application"

# プロジェクトを選択
gcloud config set project reacha-app-YYYYMMDDHHMMSS
```

### ステップ2: 課金アカウントのリンク

**重要**: Cloud Runなどのサービスを使用するには、課金アカウントが必要です。

#### 方法1: Google Cloud Consoleから

1. https://console.cloud.google.com/billing にアクセス
2. 「課金アカウントをリンク」をクリック
3. 既存の課金アカウントを選択、または新規作成
4. プロジェクトを選択してリンク

#### 方法2: コマンドラインから

```powershell
# 課金アカウントの一覧を確認
gcloud billing accounts list

# プロジェクトにリンク（BILLING_ACCOUNT_IDを実際のIDに置き換え）
gcloud billing projects link YOUR_PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

### ステップ3: 必要なAPIの有効化

```powershell
# Cloud Run API
gcloud services enable run.googleapis.com

# Container Registry API
gcloud services enable containerregistry.googleapis.com

# Cloud Build API（オプション）
gcloud services enable cloudbuild.googleapis.com
```

---

## Docker Desktop のインストール

### ステップ1: Docker Desktop のダウンロードとインストール

1. **ダウンロード**
   - https://www.docker.com/products/docker-desktop/ にアクセス
   - 「Download for Windows」をクリック

2. **インストール**
   - ダウンロードした `.exe` ファイルを実行
   - インストール時に「Use WSL 2 instead of Hyper-V」を推奨（Windows 11の場合）

3. **起動と確認**
   - Docker Desktopを起動
   - システムトレイにDockerアイコンが表示されるまで待つ
   - PowerShellで確認：
     ```powershell
     docker version
     ```

### ステップ2: Docker認証の設定

```powershell
# Google Container Registry用の認証を設定
gcloud auth configure-docker gcr.io --quiet
```

---

## デプロイの実行

### ステップ1: フロントエンドのビルド

```powershell
# flontディレクトリに移動
cd flont

# 依存関係のインストール（初回のみ）
npm install

# 静的ファイルをビルド
npm run build

# プロジェクトルートに戻る
cd ..
```

**確認**: `flont/out/` ディレクトリに静的ファイルが生成されていることを確認

### ステップ2: デプロイスクリプトの実行

```powershell
# デプロイスクリプトを実行
.\deploy.ps1
```

このスクリプトは以下を自動実行します：
1. フロントエンドのビルド（既に完了している場合はスキップ）
2. Dockerイメージのビルド
3. Container Registryへのプッシュ
4. Cloud Runへのデプロイ

### 開発環境のoutputsを含める

デプロイ時には、開発環境で生成された `back/outputs/` の内容がDockerイメージに含まれ、Cloud Runでも参照できます。

- **デプロイ時**: 開発環境のoutputsがイメージに含まれ、初回起動時に `/tmp/outputs` にコピーされます
- **デプロイ後**: Cloud Run側で生成される新しい結果のみが `/tmp/outputs` に保存されます
- **同期**: デプロイ後の開発環境の変更は反映されません（デプロイ時に一度だけコピー）

### デプロイスクリプトの内容

`deploy.ps1` は以下の処理を実行します：

```powershell
# 1. プロジェクトIDの確認
$PROJECT_ID = gcloud config get-value project

# 2. フロントエンドのビルド
cd flont
npm run build
cd ..

# 3. Dockerイメージのビルド
docker build -t gcr.io/$PROJECT_ID/reacha-app:latest .

# 4. Docker認証とプッシュ
gcloud auth configure-docker gcr.io --quiet
docker push gcr.io/$PROJECT_ID/reacha-app:latest

# 5. Cloud Runにデプロイ
gcloud run deploy reacha-app \
  --image gcr.io/$PROJECT_ID/reacha-app:latest \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10
```

### デプロイ完了の確認

デプロイが成功すると、以下のような出力が表示されます：

```
Service [reacha-app] revision [reacha-app-00001-xxx] has been deployed and is serving 100 percent of traffic.
Service URL: https://reacha-app-xxxxx.asia-northeast1.run.app
```

ブラウザでこのURLにアクセスして、アプリケーションが正常に動作することを確認してください。

---

## 環境変数の設定

デプロイ後、Dify APIキーなどの機密情報を環境変数として設定します。

### 環境変数の設定方法

```powershell
gcloud run services update reacha-app `
  --region asia-northeast1 `
  --update-env-vars `
    DIFY_API_KEY1=your_dify_api_key_1,`
    DIFY_API_KEY2=your_dify_api_key_2,`
    DIFY_USER_ID=REACHA_agent
```

### 設定可能な環境変数

| 環境変数 | 説明 | 必須 |
|---------|------|------|
| `DIFY_API_KEY1` | Dify Chat APIキー | はい |
| `DIFY_API_KEY2` | Dify Workflow APIキー | はい |
| `DIFY_USER_ID` | DifyユーザーID | いいえ（デフォルト: REACHA_agent） |
| `OUTPUTS_ROOT` | 出力ファイルの保存先 | いいえ（デフォルト: /tmp/outputs） |
| `PORT` | アプリケーションのポート | いいえ（Cloud Runが自動設定） |

**注意**: Cloud Runは一時的なストレージ（`/tmp`）のみ提供します。永続的なストレージが必要な場合は、Cloud Storageの使用を検討してください。

---

## トラブルシューティング

### 問題1: `gcloud` コマンドが見つからない

**症状**:
```
gcloud : 用語 'gcloud' は、コマンドレット、関数、スクリプト ファイル、または操作可能なプログラムの名前として認識されません。
```

**解決方法**:
1. 新しいPowerShellを開く（PATHが更新されるため）
2. PATHを手動で更新：
   ```powershell
   .\gcloud\scripts\refresh_path.ps1
   ```
3. それでも解決しない場合、手動でPATHに追加：
   - Windowsキー + R → `sysdm.cpl` → Enter
   - 「詳細設定」→「環境変数」
   - 「システム環境変数」の「Path」を編集
   - `C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin` を追加

### 問題2: Pythonが見つからない

**症状**:
```
To use the Google Cloud CLI, you must have Python installed and on your PATH.
```

**解決方法**:
1. Pythonがインストールされているか確認：
   ```powershell
   python --version
   ```
2. 環境変数 `CLOUDSDK_PYTHON` を設定：
   ```powershell
   $env:CLOUDSDK_PYTHON = "C:\Users\YourName\AppData\Local\Programs\Python\Python312\python.exe"
   [System.Environment]::SetEnvironmentVariable("CLOUDSDK_PYTHON", $env:CLOUDSDK_PYTHON, "User")
   ```
3. 自動修正スクリプトを実行：
   ```powershell
   .\gcloud\scripts\fix_gcloud_setup.ps1
   ```

### 問題3: Docker認証エラー

**症状**:
```
error from registry: Unauthenticated request.
```

**解決方法**:
```powershell
# Docker認証を設定
gcloud auth configure-docker gcr.io --quiet
```

### 問題4: PORT環境変数のエラー

**症状**:
```
ERROR: (gcloud.run.deploy) spec.template.spec.containers[0].env: The following reserved env names were provided: PORT.
```

**解決方法**:
- Cloud Runは自動的に `PORT` 環境変数を設定するため、手動で設定する必要はありません
- `deploy.ps1` から `--set-env-vars PORT=8080` を削除（既に修正済み）

### 問題5: 課金アカウントが設定されていない

**症状**:
```
ERROR: (gcloud.services.enable) FAILED_PRECONDITION: Billing account for project 'xxx' is not found.
```

**解決方法**:
1. 課金アカウントを確認：
   ```powershell
   gcloud billing accounts list
   ```
2. プロジェクトにリンク：
   ```powershell
   gcloud billing projects link YOUR_PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
   ```

### 問題6: 一時ファイルへのアクセス拒否

**症状**:
```
アクセスが拒否されました。
指定されたファイルが見つかりません。
C:\Program Files (x86)\Google\Cloud SDK\tmpfile
```

**解決方法**:
1. 管理者権限でPowerShellを実行
2. 一時ディレクトリを作成：
   ```powershell
   New-Item -ItemType Directory -Force -Path "C:\Program Files (x86)\Google\Cloud SDK\tmp"
   ```

---

## 更新デプロイ

コードを更新した場合、以下の手順で再デプロイします。

### 手順1: フロントエンドの再ビルド

```powershell
cd flont
npm run build
cd ..
```

### 手順2: デプロイスクリプトの実行

```powershell
.\deploy.ps1
```

### 手順3: デプロイの確認

```powershell
# サービスの状態を確認
gcloud run services describe reacha-app --region asia-northeast1

# ログを確認
gcloud run services logs read reacha-app --region asia-northeast1 --limit 50
```

---

## 主要コマンドリファレンス

### プロジェクト管理

```powershell
# プロジェクト一覧
gcloud projects list

# 現在のプロジェクトを確認
gcloud config get-value project

# プロジェクトを切り替え
gcloud config set project PROJECT_ID
```

### サービス管理

```powershell
# サービスの一覧
gcloud run services list --region asia-northeast1

# サービスの詳細
gcloud run services describe reacha-app --region asia-northeast1

# サービスのURLを取得
gcloud run services describe reacha-app --region asia-northeast1 --format 'value(status.url)'
```

### ログの確認

```powershell
# リアルタイムログ
gcloud run services logs tail reacha-app --region asia-northeast1

# 最近のログ
gcloud run services logs read reacha-app --region asia-northeast1 --limit 50
```

### 環境変数の管理

```powershell
# 環境変数を設定
gcloud run services update reacha-app `
  --region asia-northeast1 `
  --update-env-vars KEY1=value1,KEY2=value2

# 環境変数を削除
gcloud run services update reacha-app `
  --region asia-northeast1 `
  --remove-env-vars KEY1
```

---

## コストの見積もり

Cloud Runは従量課金制です：

- **無料枠**: 毎月200万リクエスト、360,000 GiB秒、180,000 vCPU秒
- **超過分**: 
  - リクエスト数: 100万リクエストあたり約$0.40
  - CPU時間: vCPU時間あたり約$0.00002400/秒
  - メモリ: GiB秒あたり約$0.00000250/秒

詳細: https://cloud.google.com/run/pricing

---

## セキュリティのベストプラクティス

1. **環境変数の管理**: 機密情報はSecret Managerを使用
   ```powershell
   # Secret Managerにシークレットを保存
   echo -n "your_api_key" | gcloud secrets create dify-api-key-1 --data-file=-
   
   # Cloud Runでシークレットを使用
   gcloud run services update reacha-app `
     --region asia-northeast1 `
     --update-secrets DIFY_API_KEY1=dify-api-key-1:latest
   ```

2. **認証の有効化**: 本番環境では認証を有効にしてください
   ```powershell
   gcloud run services update reacha-app `
     --region asia-northeast1 `
     --no-allow-unauthenticated
   ```

3. **HTTPS**: Cloud Runは自動的にHTTPSを提供します

---

## 参考リンク

- [Google Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Google Cloud SDK インストールガイド](https://cloud.google.com/sdk/docs/install)
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
- [Cloud Run 料金](https://cloud.google.com/run/pricing)

---

## まとめ

このガイドに従うことで、REACHAアプリケーションをGoogle Cloud Runにデプロイできます。問題が発生した場合は、トラブルシューティングセクションを参照してください。

デプロイが完了したら、サービスURLにアクセスしてアプリケーションが正常に動作することを確認してください。

