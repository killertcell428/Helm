# Google Cloud Run へのデプロイガイド

このガイドでは、REACHAアプリケーションをGoogle Cloud Runにデプロイする手順を説明します。

## 📋 前提条件

1. **Google Cloud アカウント**: Google Cloud Platform (GCP) のアカウントが必要です
2. **Google Cloud CLI**: `gcloud` コマンドラインツールがインストールされていること
3. **Docker**: ローカルでDockerイメージをビルドする場合（オプション）

## 🚀 ステップ1: Google Cloud プロジェクトの準備

### 1.1 Google Cloud プロジェクトの作成（初回のみ）

```bash
# Google Cloudにログイン
gcloud auth login

# 既存のプロジェクト一覧を表示
gcloud projects list

# プロジェクトを作成（PROJECT_IDは任意の名前に変更してください）
gcloud projects create reacha-app-20251224141452 --name="REACHA Project"

# プロジェクトを選択
gcloud config set project reacha-app-20251224141452
```

### 1.2 必要なAPIの有効化

```bash
# Cloud Run APIを有効化
gcloud services enable run.googleapis.com

# Container Registry APIを有効化（イメージ保存用）
gcloud services enable containerregistry.googleapis.com

# Cloud Build APIを有効化（自動デプロイ用、オプション）
gcloud services enable cloudbuild.googleapis.com
```

### 1.3 課金アカウントの設定

Google Cloud Console (https://console.cloud.google.com) にアクセスして、課金アカウントを設定してください。

## 🏗️ ステップ2: フロントエンドのビルド

デプロイ前に、Next.jsの静的ファイルをビルドする必要があります。

```bash
# flontディレクトリに移動
cd flont

# 依存関係のインストール（初回のみ）
npm install

# 静的ファイルをビルド
npm run build

# プロジェクトルートに戻る
cd ..
```

これで `flont/out/` ディレクトリに静的ファイルが生成されます。

## 🐳 ステップ3: Dockerイメージのビルドとプッシュ

### 3.1 ローカルでビルド（テスト用）

```bash
# Dockerイメージをビルド
docker build -t reacha-app .

# ローカルでテスト（オプション）
docker run -p 8080:8080 reacha-app
```

### 3.2 Google Container Registryにプッシュ

```bash
# プロジェクトIDを設定（YOUR_PROJECT_IDを実際のプロジェクトIDに置き換え）
export PROJECT_ID=YOUR_PROJECT_ID

# Container Registry用のイメージタグを設定
docker tag reacha-app gcr.io/$PROJECT_ID/reacha-app:latest

# Container Registryにプッシュ
docker push gcr.io/$PROJECT_ID/reacha-app:latest
```

## ☁️ ステップ4: Cloud Runにデプロイ

### 4.1 基本的なデプロイ

```bash
# Cloud Runにデプロイ
gcloud run deploy reacha-app \
  --image gcr.io/$PROJECT_ID/reacha-app:latest \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10 \
  --set-env-vars PORT=8080
```

### 4.2 環境変数の設定

Dify APIキーなどの機密情報は環境変数として設定します：

```bash
gcloud run services update reacha-app \
  --region asia-northeast1 \
  --update-env-vars \
    DIFY_API_KEY1=your_dify_api_key_1,\
    DIFY_API_KEY2=your_dify_api_key_2,\
    DIFY_USER_ID=REACHA_agent,\
    OUTPUTS_ROOT=/tmp/outputs,\
    PORT=8080
```

**重要**: Cloud Runは一時的なストレージ（`/tmp`）のみ提供します。永続的なストレージが必要な場合は、Cloud Storageを使用する必要があります。

#### 4.2.1 Cloud Storageの設定（推奨）

デプロイ後のoutputsを永続化するために、Cloud Storageを使用することを推奨します：

1. **Cloud Storageバケットの作成**:

**Linux/Mac (Bash):**
```bash
# バケット名を設定（プロジェクトIDを含む一意の名前）
export BUCKET_NAME=your-project-id-reacha-outputs

# バケットを作成
gsutil mb -p YOUR_PROJECT_ID -l asia-northeast1 gs://${BUCKET_NAME}

# Cloud Runサービスアカウントに権限を付与
export PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

**Windows (PowerShell):**
```powershell
# バケット名を設定（プロジェクトIDを含む一意の名前）
$env:BUCKET_NAME = "reacha-app-20251224141452-reacha-outputs"

# バケットを作成
gsutil mb -p reacha-app-20251224141452 -l asia-northeast1 "gs://$env:BUCKET_NAME"

# Cloud Runサービスアカウントに権限を付与
$env:PROJECT_NUMBER = gcloud projects describe reacha-app-20251224141452 --format="value(projectNumber)"
gcloud projects add-iam-policy-binding reacha-app-20251224141452 `
  --member="serviceAccount:$env:PROJECT_NUMBER-compute@developer.gserviceaccount.com" `
  --role="roles/storage.objectAdmin"
```

2. **環境変数にバケット名を設定**:

**Linux/Mac (Bash):**
```bash
gcloud run services update reacha-app \
  --region asia-northeast1 \
  --update-env-vars \
    GCS_BUCKET_NAME=${BUCKET_NAME},\
    DIFY_API_KEY1=your_dify_api_key_1,\
    DIFY_API_KEY2=your_dify_api_key_2,\
    DIFY_USER_ID=REACHA_agent,\
    OUTPUTS_ROOT=/tmp/outputs,\
    PORT=8080
```

**Windows (PowerShell):**
```powershell
$env:BUCKET_NAME = "reacha-app-20251224141452-reacha-outputs"
gcloud run services update reacha-app `
  --region asia-northeast1 `
  --update-env-vars `
    "GCS_BUCKET_NAME=$env:BUCKET_NAME",`
    "DIFY_API_KEY1=app-BfDFjZRyj3qBakTTxVZNOt1J",`
    "DIFY_API_KEY2=app-dI8MOoihsJo04pNh2fzfehtd",`
    "DIFY_USER_ID=REACHA_agent",`
    "OUTPUTS_ROOT=/tmp/outputs",`
    "PORT=8080"
```



**注意**: `GCS_BUCKET_NAME`が設定されている場合、アプリケーションは自動的にCloud Storageを使用します。設定されていない場合は、従来通りローカルファイルシステム（`/tmp/outputs`）を使用します。

**メリット**:
- デプロイ後もoutputsが保持される
- 複数のリビジョン間で共有可能
- バックアップと復元が容易

### 4.3 認証の設定（オプション）

認証を有効にする場合：

```bash
gcloud run services update reacha-app \
  --region asia-northeast1 \
  --no-allow-unauthenticated \
  --update-env-vars \
    AUTH_TOKEN=your_secret_token
```

## 📝 ステップ5: デプロイの確認

### 5.1 サービスのURLを取得

```bash
gcloud run services describe reacha-app \
  --region asia-northeast1 \
  --format 'value(status.url)'
```

### 5.2 動作確認

ブラウザで上記のURLにアクセスして、アプリケーションが正常に動作することを確認してください。

## 🔄 ステップ6: 更新デプロイ

コードを更新した場合：

```bash
# 1. フロントエンドを再ビルド
cd flont
npm run build
cd ..

# 2. Dockerイメージを再ビルド
docker build -t reacha-app .

# 3. 新しいタグでプッシュ
docker tag reacha-app gcr.io/$PROJECT_ID/reacha-app:latest
docker push gcr.io/$PROJECT_ID/reacha-app:latest

# 4. Cloud Runを更新
gcloud run deploy reacha-app \
  --image gcr.io/$PROJECT_ID/reacha-app:latest \
  --region asia-northeast1 \
  --platform managed
```

## 🎯 自動デプロイ（Cloud Build使用、オプション）

GitHubと連携して自動デプロイする場合：

### 6.1 Cloud Buildトリガーの設定

```bash
# Cloud Buildトリガーを作成
gcloud builds triggers create github \
  --repo-name=YOUR_REPO_NAME \
  --repo-owner=YOUR_GITHUB_USERNAME \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

### 6.2 GitHub連携

1. Google Cloud Consoleで「Cloud Build」→「トリガー」に移動
2. 「GitHubを接続」をクリック
3. 認証を完了
4. リポジトリを選択

## ⚙️ 設定のカスタマイズ

### リソースの調整

```bash
# メモリとCPUを増やす
gcloud run services update reacha-app \
  --region asia-northeast1 \
  --memory 4Gi \
  --cpu 4

# 同時実行数を制限
gcloud run services update reacha-app \
  --region asia-northeast1 \
  --max-instances 5 \
  --concurrency 10
```

### タイムアウトの調整

長時間実行するジョブがある場合：

```bash
gcloud run services update reacha-app \
  --region asia-northeast1 \
  --timeout 3600  # 最大3600秒（1時間）
```

**注意**: Cloud Runの最大タイムアウトは3600秒（1時間）です。それ以上の長時間実行が必要な場合は、別のアーキテクチャを検討してください。

## 📊 ログの確認

```bash
# リアルタイムログを表示
gcloud run services logs tail reacha-app \
  --region asia-northeast1

# 最近のログを表示
gcloud run services logs read reacha-app --region asia-northeast1 --limit 50
```

## 🔒 セキュリティのベストプラクティス

1. **環境変数の管理**: 機密情報はSecret Managerを使用
   ```bash
   # Secret Managerにシークレットを保存
   echo -n "your_api_key" | gcloud secrets create dify-api-key-1 --data-file=-
   
   # Cloud Runでシークレットを使用
   gcloud run services update reacha-app \
     --region asia-northeast1 \
     --update-secrets DIFY_API_KEY1=dify-api-key-1:latest
   ```

2. **認証の有効化**: 本番環境では認証を有効にしてください

3. **HTTPS**: Cloud Runは自動的にHTTPSを提供します

## 💰 コストの見積もり

Cloud Runは従量課金制です：
- **リクエスト数**: 100万リクエストあたり約$0.40
- **CPU時間**: vCPU時間あたり約$0.00002400/秒
- **メモリ**: GiB秒あたり約$0.00000250/秒

詳細: https://cloud.google.com/run/pricing

## 🐛 トラブルシューティング

### デプロイが失敗する場合

```bash
# ビルドログを確認
gcloud builds list --limit=5

# 詳細なログを確認
gcloud builds log BUILD_ID
```

### アプリケーションが起動しない場合

```bash
# ログを確認
gcloud run services logs read reacha-app \
  --region asia-northeast1 \
  --limit 100
```

### ポートエラー

Cloud Runは環境変数`PORT`で指定されたポートでリッスンする必要があります。`main.py`で`PORT=8080`が設定されていることを確認してください。

## 📚 参考リンク

- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Cloud Run クイックスタート](https://cloud.google.com/run/docs/quickstarts/build-and-deploy)
- [Container Registry ドキュメント](https://cloud.google.com/container-registry/docs)

## ❓ よくある質問

**Q: 永続的なストレージは使えますか？**  
A: Cloud Runは一時的なストレージ（`/tmp`）のみ提供します。永続的なストレージが必要な場合は、Cloud Storageを使用してください。

**Q: 長時間実行（30-40分）は可能ですか？**  
A: Cloud Runの最大タイムアウトは3600秒（1時間）です。それ以内であれば可能です。

**Q: 複数のインスタンスが同時に実行されますか？**  
A: はい、リクエスト数に応じて自動的にスケールします。`--max-instances`で最大数を制限できます。

---

**デプロイに関する質問や問題があれば、ログを確認するか、Google Cloudサポートにお問い合わせください。**
