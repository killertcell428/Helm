# Google Cloud Run デプロイ関連ファイル

このフォルダには、REACHAアプリケーションをGoogle Cloud Runにデプロイするためのドキュメントとスクリプトが含まれています。

## フォルダ構成

```
gcloud/
├── docs/              # ドキュメント類
├── scripts/           # セットアップ・修正スクリプト
├── cloudbuild.yaml    # Cloud Build設定（CI/CD用）
└── README.md         # このファイル
```

## 主要ファイル

### ドキュメント（docs/）

- **DEPLOYMENT_GUIDE.md** - 完全なデプロイ手順書
- **ARCHITECTURE_DESIGN.md** - システムアーキテクチャ設計書
- **BLOG_CURSOR_GCLOUD.md** - ブログ記事「Cursor エディターのみでGoogle cloud を始めたい！」
- **DEPLOY_GCLOUD.md** - デプロイガイド（詳細版）
- **SETUP_GCLOUD_WINDOWS.md** - Windows環境でのセットアップガイド
- **INSTALL_GCLOUD.md** - Google Cloud SDKインストールガイド
- **SETUP_BILLING.md** - 課金アカウント設定ガイド
- **CHECK_DOCKER.md** - Dockerセットアップガイド
- **QUICK_FIX.md** - クイック修正ガイド
- **README_DEPLOY.md** - クイックスタートガイド
- **DEPLOY_GCLOUD_API_KEY.md** - APIキー設定ガイド
- **OUTPUTS_SYNC.md** - 開発環境のoutputs同期について
- **LOGGING_AND_MONITORING.md** - ログの見方・Cloud Run モニタリング
- **ENV_VARS_REFERENCE.md** - 環境変数一覧
- **NEXT_ACTIONS.md** - 次のアクション（優先順位順）

### スクリプト（scripts/）

- **fix_gcloud_setup.ps1** - Google Cloud CLI設定修正スクリプト
- **setup_project.ps1** - プロジェクト作成とAPI有効化スクリプト
- **refresh_path.ps1** - PATH環境変数更新スクリプト

### 設定ファイル

- **cloudbuild.yaml** - Cloud Build設定（CI/CD用、オプション）

## プロジェクトルートに残すファイル

以下のファイルは、パスの関係でプロジェクトルートに残しています：

- **deploy.ps1** - メインデプロイスクリプト（プロジェクトルートから実行）
- **deploy.sh** - メインデプロイスクリプト（Linux/Mac用）
- **Dockerfile** - コンテナイメージ定義
- **.dockerignore** - Dockerビルド除外設定
- **.gcloudignore** - Cloud Build除外設定

## 使い方

### 初回セットアップ

1. **Google Cloud CLIの設定**
   ```powershell
   .\gcloud\scripts\fix_gcloud_setup.ps1
   ```

2. **プロジェクトの作成**
   ```powershell
   .\gcloud\scripts\setup_project.ps1
   ```

3. **デプロイの実行**
   ```powershell
   .\deploy.ps1
   ```

### ドキュメントの参照

詳細な手順は `gcloud\docs\DEPLOYMENT_GUIDE.md` を参照してください。

## トラブルシューティング

問題が発生した場合は、`gcloud\docs\` 内のトラブルシューティングガイドを参照してください。

