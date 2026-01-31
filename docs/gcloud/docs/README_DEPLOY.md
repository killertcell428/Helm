# 🚀 クイックスタート: Google Cloud Run へのデプロイ

このドキュメントは、REACHAアプリケーションをGoogle Cloud Runにデプロイするための**簡易ガイド**です。  
詳細な手順は [`DEPLOY_GCLOUD.md`](./DEPLOY_GCLOUD.md) を参照してください。

## ⚡ 5分でデプロイ

### 前提条件
- Google Cloud アカウント
- `gcloud` CLI がインストール済み
- Docker がインストール済み（ローカルビルドの場合）

### 1. プロジェクトの設定

```bash
# Google Cloudにログイン
gcloud auth login

# プロジェクトを作成・選択
gcloud projects create YOUR_PROJECT_ID
gcloud config set project YOUR_PROJECT_ID

# 必要なAPIを有効化
gcloud services enable run.googleapis.com containerregistry.googleapis.com
```

### 2. デプロイスクリプトの実行

**Windows (PowerShell):**
```powershell
.\deploy.ps1
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

これで完了です！スクリプトが以下を自動実行します：
1. フロントエンドのビルド
2. Dockerイメージのビルド
3. Container Registryへのプッシュ
4. Cloud Runへのデプロイ

### 3. 環境変数の設定

デプロイ後、Dify APIキーを設定：

```bash
gcloud run services update reacha-app \
  --region asia-northeast1 \
  --update-env-vars \
    DIFY_API_KEY1=your_key_1,\
    DIFY_API_KEY2=your_key_2,\
    DIFY_USER_ID=REACHA_agent
```

## 📝 重要な注意事項

### 永続ストレージについて

**Cloud Runは一時的なストレージ（`/tmp`）のみ提供します。**

現在の実装では、出力ファイルは以下の場所に保存されます：
- デフォルト: `back/outputs/` （ローカル開発時）
- Cloud Run: `/tmp/outputs/` （環境変数 `OUTPUTS_ROOT=/tmp/outputs` を設定）

**⚠️ 注意**: `/tmp` のデータはコンテナ再起動時に削除されます。

**永続化が必要な場合の選択肢：**
1. **Cloud Storage**: 出力ファイルをCloud Storageに保存するようにコードを修正
2. **Cloud SQL / Firestore**: データベースに保存
3. **Cloud Filestore**: 共有ファイルシステム（高コスト）

### タイムアウト制限

Cloud Runの最大タイムアウトは **3600秒（1時間）** です。
- 現在の設定: `--timeout 3600`
- それ以上の長時間実行が必要な場合は、別のアーキテクチャを検討してください

### コスト

Cloud Runは従量課金制です：
- リクエストがない間は課金されません
- リクエスト処理中のみ課金されます
- 詳細: https://cloud.google.com/run/pricing

## 🔧 トラブルシューティング

### デプロイが失敗する

```bash
# ログを確認
gcloud run services logs read reacha-app --region asia-northeast1 --limit 50
```

### アプリケーションが起動しない

1. 環境変数 `PORT=8080` が設定されているか確認
2. ログでエラーメッセージを確認
3. ローカルでDockerイメージをテスト: `docker run -p 8080:8080 gcr.io/YOUR_PROJECT_ID/reacha-app:latest`

### フロントエンドが表示されない

`flont/out/` ディレクトリが正しくビルドされているか確認：
```bash
cd flont
npm run build
ls -la out/  # ファイルが存在するか確認
```

## 📚 詳細ドキュメント

- 詳細な手順: [`DEPLOY_GCLOUD.md`](./DEPLOY_GCLOUD.md)
- Google Cloud Run ドキュメント: https://cloud.google.com/run/docs

## 💡 次のステップ

1. **認証の設定**: 本番環境では認証を有効化
2. **カスタムドメイン**: 独自ドメインの設定
3. **CI/CD**: GitHub ActionsやCloud Buildでの自動デプロイ
4. **モニタリング**: Cloud Monitoringでの監視設定

---

**質問や問題があれば、[`DEPLOY_GCLOUD.md`](./DEPLOY_GCLOUD.md) のトラブルシューティングセクションを参照してください。**
