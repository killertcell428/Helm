# クイックスタートガイド

Helm Backend APIを5分でCloud Runにデプロイする簡易ガイドです。

## 前提条件

- [ ] Google Cloud CLIがインストール済み
- [ ] Docker Desktopが起動中
- [ ] Google Cloudアカウントがある
- [ ] 既存プロジェクト `helm-project-484105` を使用

## ステップ1: 前提条件の確認（1分）

### Google Cloud CLIの確認

```powershell
gcloud version
```

**エラーが出る場合**: [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) をインストール

### Dockerの確認

```powershell
docker version
```

**エラーが出る場合**: Docker Desktopを起動

### プロジェクトの設定

```powershell
gcloud config set project helm-project-484105
gcloud auth login
```

## ステップ2: 必要な設定の確認（2分）

### 課金アカウントの確認

```powershell
gcloud billing projects describe helm-project-484105
```

**エラーが出る場合**: [課金アカウントページ](https://console.cloud.google.com/billing) でリンク

### 必要なAPIの有効化

```powershell
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## ステップ3: デプロイの実行（2分）

### デプロイスクリプトの実行

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

### デプロイ完了の確認

デプロイが成功すると、以下のような出力が表示されます：

```
=== Deployment Complete ===

Service URL: https://helm-api-xxxxx.asia-northeast1.run.app

Next steps:
1. Set environment variables (see MANUAL_SETUP_GUIDE.md)
2. Test the API: https://helm-api-xxxxx.asia-northeast1.run.app/docs
3. Check logs: gcloud run services logs read helm-api --region asia-northeast1
```

## ステップ4: 環境変数の設定（必須）

デプロイ後、以下の環境変数を設定してください：

### 必須環境変数

```powershell
gcloud run services update helm-api `
  --region asia-northeast1 `
  --update-env-vars `
    "GOOGLE_API_KEY=your-api-key-here,USE_LLM=true,GOOGLE_CLOUD_PROJECT_ID=helm-project-484105,OUTPUT_DIR=/tmp/outputs"
```

**重要**: 
- `your-api-key-here` を実際のGemini APIキーに置き換えてください
- APIキーは [Google AI Studio](https://makersuite.google.com/app/apikey) で取得できます

### OAuth認証を使用する場合（オプション）

```powershell
gcloud run services update helm-api `
  --region asia-northeast1 `
  --update-env-vars `
    "GOOGLE_OAUTH_CREDENTIALS_FILE=/tmp/oauth-credentials.json,GOOGLE_DRIVE_FOLDER_ID=your-folder-id"
```

**詳細**: [手作業セットアップガイド](./MANUAL_SETUP_GUIDE.md) の「OAuth認証情報の取得」セクションを参照

## ステップ5: 動作確認（1分）

### APIドキュメントの確認

ブラウザで以下のURLにアクセス：
```
https://helm-api-xxxxx.asia-northeast1.run.app/docs
```

### ヘルスチェック

```powershell
curl https://helm-api-xxxxx.asia-northeast1.run.app/
```

**期待される出力**:
```json
{"status":"ok","message":"Helm API is running"}
```

### ログの確認

```powershell
gcloud run services logs read helm-api --region asia-northeast1 --limit 20
```

## 完了！

デプロイが完了しました。次は以下を確認してください：

- [デプロイ後確認手順](./POST_DEPLOY_CHECK.md) で詳細な動作確認
- [環境変数リファレンス](./ENV_VARS_REFERENCE.md) で環境変数の詳細を確認
- [トラブルシューティング](./TROUBLESHOOTING.md) で問題を解決

## よくある質問

### Q: デプロイに時間がかかりますか？

A: 初回デプロイは5-10分かかることがあります。2回目以降は3-5分程度です。

### Q: 環境変数を後で設定できますか？

A: はい。デプロイ後、いつでも環境変数を追加・更新できます。

### Q: デプロイが失敗しました

A: [トラブルシューティング](./TROUBLESHOOTING.md) を参照してください。

### Q: サービスURLが表示されません

A: 以下のコマンドで取得できます：
```powershell
gcloud run services describe helm-api --region asia-northeast1 --format="value(status.url)"
```

## 次のステップ

- [手作業セットアップガイド](./MANUAL_SETUP_GUIDE.md) で詳細な設定手順を確認
- [デプロイ前チェックリスト](./DEPLOY_CHECKLIST.md) で設定を確認
- [デプロイ後確認手順](./POST_DEPLOY_CHECK.md) で動作を確認

---

**5分でデプロイ完了！お疲れ様でした！** 🎉
