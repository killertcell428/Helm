# Helm Backend API 手作業セットアップガイド

このドキュメントは、Helm Backend APIをGoogle Cloud Runにデプロイするために必要な**手作業での設定手順**を説明します。  
デプロイスクリプト（`deploy.ps1`）を実行する前に、このガイドに従って必要な設定を完了してください。

## 目次

1. [前提条件の確認](#前提条件の確認)
2. [Google Cloud Consoleでの設定](#google-cloud-consoleでの設定)
3. [APIキーの取得](#apiキーの取得)
4. [OAuth認証情報の取得](#oauth認証情報の取得)
5. [環境変数の設定](#環境変数の設定)
6. [デプロイの実行](#デプロイの実行)

---

## 前提条件の確認

### 1. Google Cloud CLIのインストール確認

```powershell
gcloud version
```

**エラーが出る場合**:  
Google Cloud SDKをインストールしてください。  
https://cloud.google.com/sdk/docs/install

### 2. Docker Desktopの起動確認

```powershell
docker version
```

**エラーが出る場合**:  
Docker Desktopを起動してください。  
https://www.docker.com/products/docker-desktop/

### 3. 既存プロジェクトの確認

```powershell
gcloud config get-value project
```

**出力が `helm-project-484105` でない場合**:

```powershell
gcloud config set project helm-project-484105
```

---

## Google Cloud Consoleでの設定

### ステップ1: プロジェクトの選択

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクト選択ドロップダウンから **`helm-project-484105`** を選択

### ステップ2: 課金アカウントのリンク確認

1. [課金アカウントページ](https://console.cloud.google.com/billing) にアクセス
2. プロジェクト `helm-project-484105` に課金アカウントがリンクされているか確認

**リンクされていない場合**:

1. 「課金アカウントをリンク」をクリック
2. 既存の課金アカウントを選択、または新規作成
3. プロジェクト `helm-project-484105` を選択してリンク

**コマンドラインから確認**:

```powershell
gcloud billing accounts list
gcloud billing projects describe helm-project-484105
```

### ステップ3: 必要なAPIの有効化

以下のAPIが有効化されているか確認します。  
[APIとサービス](https://console.cloud.google.com/apis/library) ページで確認できます。

#### 必須API

- **Cloud Run API** (`run.googleapis.com`)
- **Container Registry API** (`containerregistry.googleapis.com`)

#### オプションAPI（機能によって必要）

- **Cloud Build API** (`cloudbuild.googleapis.com`) - Cloud Build使用時
- **Vertex AI API** (`aiplatform.googleapis.com`) - LLM使用時
- **Google Drive API** (`drive.googleapis.com`) - OAuth認証使用時
- **Google Chat API** (`chat.googleapis.com`) - Google Chat統合使用時
- **Google Meet API** (`meet.googleapis.com`) - Google Meet統合使用時

**コマンドラインから有効化**:

```powershell
# 必須API
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# オプションAPI（必要に応じて）
gcloud services enable cloudbuild.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable drive.googleapis.com
gcloud services enable chat.googleapis.com
gcloud services enable meet.googleapis.com
```

**確認方法**:

```powershell
gcloud services list --enabled --project=helm-project-484105
```

---

## APIキーの取得

### Gemini APIキーの取得（必須）

HelmアプリはADK（Agent Development Kit）とGemini APIを使用するため、APIキーが必要です。

#### 手順

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. プロジェクトを選択（`helm-project-484105` を推奨）
5. APIキーが生成されるので、**すぐにコピーして安全な場所に保存**

**重要**:  
- APIキーは一度しか表示されません
- 漏洩した場合は、すぐに無効化して新しいキーを生成してください

#### 保存方法

取得したAPIキーは、後でCloud Runの環境変数として設定します。  
今のところは、メモ帳などに保存しておいてください。

**例**:  
```
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## OAuth認証情報の取得

Helmアプリは個人のGoogleアカウントでGoogle Drive/Docsを使用するため、OAuth 2.0認証情報が必要です。

### ステップ1: OAuth同意画面の設定

1. [OAuth同意画面](https://console.cloud.google.com/apis/credentials/consent) にアクセス
2. プロジェクト `helm-project-484105` を選択
3. 「外部」を選択して「作成」をクリック
4. アプリ情報を入力：
   - **アプリ名**: `Helm Backend API`
   - **ユーザーサポートメール**: あなたのメールアドレス
   - **デベロッパーの連絡先情報**: あなたのメールアドレス
5. 「保存して次へ」をクリック
6. スコープは後で設定するので、「保存して次へ」をクリック
7. テストユーザーに自分のメールアドレスを追加（必要に応じて）
8. 「保存して次へ」→「ダッシュボードに戻る」

### ステップ2: OAuth 2.0 クライアントIDの作成

1. [認証情報](https://console.cloud.google.com/apis/credentials) ページにアクセス
2. 「認証情報を作成」→「OAuth クライアント ID」を選択
3. アプリケーションの種類で「ウェブアプリケーション」を選択
4. 名前を入力（例: `Helm Backend API OAuth Client`）
5. **承認済みのリダイレクト URI** を追加：
   - `http://localhost:8000`（開発環境用）
   - `https://helm-api-xxxxx.asia-northeast1.run.app`（本番環境用、デプロイ後に追加）
6. 「作成」をクリック
7. **クライアントID**と**クライアントシークレット**が表示されるので、コピーして保存

### ステップ3: JSONファイルのダウンロード

1. 作成したOAuth 2.0 クライアントIDの右側にある「ダウンロード」アイコンをクリック
2. JSONファイルがダウンロードされる
3. ファイル名を `oauth-credentials.json` にリネーム（任意）
4. 安全な場所に保存（例: `Dev/backend/credentials/oauth-credentials.json`）

**重要**:  
- JSONファイルには機密情報が含まれています
- Gitにコミットしないでください（`.gitignore`に追加済み）

### ステップ4: スコープの設定

OAuth認証で使用するスコープを設定します。

1. [OAuth同意画面](https://console.cloud.google.com/apis/credentials/consent) に戻る
2. 「スコープを追加または削除」をクリック
3. 以下のスコープを追加：
   - `https://www.googleapis.com/auth/drive` - Google Driveアクセス
   - `https://www.googleapis.com/auth/documents` - Google Docsアクセス
   - `https://www.googleapis.com/auth/chat.messages.readonly` - Google Chat読み取り
   - `https://www.googleapis.com/auth/meetings.space.readonly` - Google Meet読み取り
4. 「更新」→「保存して次へ」

---

## 環境変数の設定

デプロイ後、Cloud Runの環境変数を設定します。

### 方法1: コマンドラインで設定（推奨）

```powershell
# デプロイ後に実行
gcloud run services update helm-api `
  --region asia-northeast1 `
  --update-env-vars `
    "GOOGLE_API_KEY=your-api-key-here,USE_LLM=true,GOOGLE_CLOUD_PROJECT_ID=helm-project-484105,GOOGLE_OAUTH_CREDENTIALS_FILE=/tmp/oauth-credentials.json,GOOGLE_DRIVE_FOLDER_ID=your-folder-id,CORS_ORIGINS=http://localhost:3000,https://*.vercel.app,OUTPUT_DIR=/tmp/outputs"
```

**注意**:  
- `your-api-key-here` を実際のGemini APIキーに置き換え
- `your-folder-id` を実際のGoogle DriveフォルダIDに置き換え
- 複数の環境変数はカンマで区切ります

### 方法2: Google Cloud Consoleから設定

1. [Cloud Run](https://console.cloud.google.com/run) ページにアクセス
2. `helm-api` サービスを選択
3. 「編集と新しいリビジョンをデプロイ」をクリック
4. 「変数とシークレット」タブを選択
5. 「変数を追加」をクリックして、以下の環境変数を追加：

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `GOOGLE_API_KEY` | `your-api-key-here` | Gemini APIキー |
| `USE_LLM` | `true` | LLM統合を有効化 |
| `GOOGLE_CLOUD_PROJECT_ID` | `helm-project-484105` | プロジェクトID |
| `GOOGLE_OAUTH_CREDENTIALS_FILE` | `/tmp/oauth-credentials.json` | OAuth認証情報ファイルパス |
| `GOOGLE_DRIVE_FOLDER_ID` | `your-folder-id` | Google DriveフォルダID |
| `CORS_ORIGINS` | `http://localhost:3000,https://*.vercel.app` | CORS許可オリジン |
| `OUTPUT_DIR` | `/tmp/outputs` | 出力ファイル保存先 |

6. 「デプロイ」をクリック

### OAuth認証情報ファイルのアップロード

OAuth認証情報のJSONファイルをCloud Runにアップロードする必要があります。

#### 方法1: Secret Managerを使用（推奨）

```powershell
# Secret Managerにシークレットを保存
echo -n "@oauth-credentials.json" | gcloud secrets create oauth-credentials --data-file=-

# Cloud Runでシークレットを使用
gcloud run services update helm-api `
  --region asia-northeast1 `
  --update-secrets GOOGLE_OAUTH_CREDENTIALS_FILE=oauth-credentials:latest
```

#### 方法2: 環境変数として直接設定（非推奨）

JSONファイルの内容をBase64エンコードして環境変数に設定する方法もありますが、セキュリティ上推奨されません。

---

## デプロイの実行

すべての設定が完了したら、デプロイスクリプトを実行します。

### ステップ1: デプロイスクリプトの実行

```powershell
cd Dev/backend
.\deploy.ps1
```

このスクリプトは以下を自動実行します：
1. プロジェクトの確認
2. Dockerの確認
3. Docker認証の設定
4. Dockerイメージのビルド
5. Container Registryへのプッシュ
6. Cloud Runへのデプロイ

### ステップ2: デプロイ完了の確認

デプロイが成功すると、以下のような出力が表示されます：

```
=== Deployment Complete ===

Service URL: https://helm-api-xxxxx.asia-northeast1.run.app

Next steps:
1. Set environment variables (see MANUAL_SETUP_GUIDE.md)
2. Test the API: https://helm-api-xxxxx.asia-northeast1.run.app/docs
3. Check logs: gcloud run services logs read helm-api --region asia-northeast1
```

### ステップ3: 環境変数の設定

デプロイ後、上記の「環境変数の設定」セクションに従って環境変数を設定してください。

### ステップ4: 動作確認

1. **APIドキュメントの確認**:  
   `https://helm-api-xxxxx.asia-northeast1.run.app/docs` にアクセス

2. **ヘルスチェック**:  
   ```powershell
   curl https://helm-api-xxxxx.asia-northeast1.run.app/
   ```

3. **ログの確認**:  
   ```powershell
   gcloud run services logs read helm-api --region asia-northeast1 --limit 50
   ```

---

## 次のステップ

- [デプロイ前チェックリスト](./DEPLOY_CHECKLIST.md) で設定を確認
- [デプロイ後確認手順](./POST_DEPLOY_CHECK.md) で動作を確認
- [トラブルシューティング](./TROUBLESHOOTING.md) で問題を解決
- [環境変数リファレンス](./ENV_VARS_REFERENCE.md) で詳細を確認

---

## 参考リンク

- [Google Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Google AI Studio](https://makersuite.google.com/app/apikey)
- [OAuth 2.0 認証情報の作成](https://console.cloud.google.com/apis/credentials)
- [Cloud Run 料金](https://cloud.google.com/run/pricing)
