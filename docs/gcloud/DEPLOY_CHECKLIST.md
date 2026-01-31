# デプロイ前チェックリスト

Helm Backend APIをCloud Runにデプロイする前に、以下の項目を確認してください。

## 前提条件

- [ ] **Google Cloud CLIがインストール済み**

  ```powershell
  gcloud version
  ```

  - エラーが出る場合: [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) をインストール

  (venv) PS C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend> gcloud version

  Google Cloud SDK 550.0.0
  bq 2.1.26
  core 2025.12.12
  gcloud-crc32c 1.0.0
  gsutil 5.35
  Updates are available for some Google Cloud CLI components.  To install them,
  please run:
    $ gcloud components update

  To take a quick anonymous survey, run:
    $ gcloud survey
- [ ] **Docker Desktopが起動中**

  ```powershell
  docker version
  ```

  - エラーが出る場合: Docker Desktopを起動

  (venv) PS C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend> docker versionClient:
   Version:           29.1.3
   API version:       1.52
   Go version:        go1.25.5
   Git commit:        f52814d
   Built:             Fri Dec 12 14:51:52 2025
   OS/Arch:           windows/amd64
   Context:           desktop-linux

  Server: Docker Desktop 4.55.0 (213807)
   Engine:
    Version:          29.1.3
    API version:      1.52 (minimum version 1.44)
    Go version:       go1.25.5
    Git commit:       fbf3ed2
    Built:            Fri Dec 12 14:49:51 2025
    OS/Arch:          linux/amd64
    Experimental:     false
   containerd:
    Version:          v2.2.0
    GitCommit:        1c4457e00facac03ce1d75f7b6777a7a851e5c41
   runc:
    Version:          1.3.4
    GitCommit:        v1.3.4-0-gd6d73eb8
   docker-init:
    Version:          0.19.0
    GitCommit:        de40ad0
- [ ] **プロジェクトが選択されている**

  ```powershell
  gcloud config get-value project
  ```

  (venv) PS C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend> gcloud config get-value project

  reacha-app-20251224141452

  Updates are available for some Google Cloud CLI components.  To install them,
  please run:
    $ gcloud components update
- [ ] 

  - 出力が `helm-project-484105` でない場合:

    ```powershell
    gcloud config set project helm-project-484105
    ```


    (venv) PS C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend> gcloud config set project helm-project-484105

    WARNING: Your active project does not match the quota project in your local Application Default Credentials file. This might result in unexpected quota issues.

    To update your Application Default Credentials quota project, use the `gcloud auth application-default set-quota-project` command.
    Updated property [core/project].
- [ ] **Google Cloudにログイン済み**

  ```powershell
  gcloud auth list
  ```

  (venv) PS C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend> gcloud auth list
       Credentialed Accounts
  ACTIVE  ACCOUNT

  * killertcell428@gmail.com

  To set the active account, run:
      $ gcloud config set account `ACCOUNT`
- [ ] 

  - ログインしていない場合:
    ```powershell
    gcloud auth login
    ```

## Google Cloud設定

- [ ] **課金アカウントがリンクされている**

  - [課金アカウントページ](https://console.cloud.google.com/billing) で確認
  - またはコマンドライン:

    ```powershell
    gcloud billing projects describe helm-project-484105
    ```

    (venv) PS C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend> gcloud billing projects describe helm-project-484105
    billingAccountName: billingAccounts/010340-684150-1DF80B
    billingEnabled: true
    name: projects/helm-project-484105/billingInfo
    projectId: helm-project-484105
- [ ] **必要なAPIが有効化されている**

  - [APIとサービス](https://console.cloud.google.com/apis/library) で確認
  - 必須API:
    - [ ] Cloud Run API (`run.googleapis.com`)
    - [ ] Container Registry API (`containerregistry.googleapis.com`)
  - オプションAPI（機能によって必要）:
    - [ ] Cloud Build API (`cloudbuild.googleapis.com`)
    - [ ] Vertex AI API (`aiplatform.googleapis.com`)
    - [ ] Google Drive API (`drive.googleapis.com`)
    - [ ] Google Chat API (`chat.googleapis.com`)
    - [ ] Google Meet API (`meet.googleapis.com`)

  **コマンドラインから確認**:

  ```powershell
  gcloud services list --enabled --project=helm-project-484105
  ```


  (venv) PS C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend> gcloud services list --enabled --project=helm-project-484105

  NAME                                 TITLE
  aiplatform.googleapis.com            Vertex AI API
  analyticshub.googleapis.com          Analytics Hub API
  bigquery.googleapis.com              BigQuery API
  bigqueryconnection.googleapis.com    BigQuery Connection API
  bigquerydatapolicy.googleapis.com    BigQuery Data Policy API
  bigquerydatatransfer.googleapis.com  BigQuery Data Transfer API
  bigquerymigration.googleapis.com     BigQuery Migration API
  bigqueryreservation.googleapis.com   BigQuery Reservation API
  bigquerystorage.googleapis.com       BigQuery Storage API
  chat.googleapis.com                  Google Chat API
  cloudapis.googleapis.com             Google Cloud APIs
  cloudtrace.googleapis.com            Cloud Trace API
  dataform.googleapis.com              Dataform API
  dataplex.googleapis.com              Cloud Dataplex API
  datastore.googleapis.com             Cloud Datastore API
  docs.googleapis.com                  Google Docs API
  drive.googleapis.com                 Google Drive API
  generativelanguage.googleapis.com    Generative Language API
  logging.googleapis.com               Cloud Logging API
  meet.googleapis.com                  Google Meet API
  monitoring.googleapis.com            Cloud Monitoring API
  servicemanagement.googleapis.com     Service Management API
  serviceusage.googleapis.com          Service Usage API
  sql-component.googleapis.com         Cloud SQL
  storage-api.googleapis.com           Google Cloud Storage JSON API
  storage-component.googleapis.com     Cloud Storage
  storage.googleapis.com               Cloud Storage API

## 認証情報の準備

- [ ] **Gemini APIキーが取得済み**

  - [Google AI Studio](https://makersuite.google.com/app/apikey) で取得
  - APIキーを安全な場所に保存
  - 値の例: `GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`
- [ ] **OAuth認証情報が取得済み**（OAuth認証を使用する場合）

  - [認証情報](https://console.cloud.google.com/apis/credentials) でOAuth 2.0 クライアントIDを作成
  - JSONファイルをダウンロードして保存
  - ファイルパスをメモ（例: `Dev/backend/credentials/oauth-credentials.json`）
- [ ] **Google DriveフォルダIDが取得済み**（OAuth認証を使用する場合）

  - Google Driveでフォルダを作成または選択
  - フォルダのURLからIDを取得
  - 例: `https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j` → ID: `1a2b3c4d5e6f7g8h9i0j`

## 環境変数の準備

以下の環境変数の値を準備してください：

- [ ] `GOOGLE_API_KEY` - Gemini APIキー
- [ ] `USE_LLM=true` - LLM統合を有効化
- [ ] `GOOGLE_CLOUD_PROJECT_ID=helm-project-484105` - プロジェクトID
- [ ] `GOOGLE_OAUTH_CREDENTIALS_FILE` - OAuth認証情報ファイルパス（OAuth使用時）
- [ ] `GOOGLE_DRIVE_FOLDER_ID` - Google DriveフォルダID（OAuth使用時）
- [ ] `CORS_ORIGINS` - フロントエンドURL（カンマ区切り）
- [ ] `OUTPUT_DIR=/tmp/outputs` - 出力ファイル保存先

**詳細**: [環境変数リファレンス](./ENV_VARS_REFERENCE.md) を参照

## コードの確認

- [ ] **Dockerfileが存在する**

  - `Dev/backend/Dockerfile` が存在することを確認
- [ ] **requirements.txtが存在する**

  - `Dev/backend/requirements.txt` が存在することを確認
- [ ] **main.pyが存在する**

  - `Dev/backend/main.py` が存在することを確認

## デプロイスクリプトの確認

- [ ] **deploy.ps1が存在する**

  - `Dev/backend/deploy.ps1` が存在することを確認
- [ ] **デプロイスクリプトの実行権限**

  - PowerShellで実行可能であることを確認

## 最終確認

すべてのチェック項目が完了したら、デプロイを実行できます：

```powershell
cd Dev/backend
.\deploy.ps1
```

## デプロイ後の確認

デプロイ後は、[デプロイ後確認手順](./POST_DEPLOY_CHECK.md) を参照してください。

## トラブルシューティング

問題が発生した場合は、[トラブルシューティングガイド](./TROUBLESHOOTING.md) を参照してください。
