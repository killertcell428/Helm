# 🎉 Cloud Runデプロイ成功！次のステップ

**デプロイ日**: 2025年1月31日
**サービスURL**: https://helm-api-dsy6lzllhq-an.a.run.app

## ✅ デプロイ完了項目

- ✅ Dockerイメージのビルド
- ✅ Container Registryへのプッシュ
- ✅ Cloud Runへのデプロイ
- ✅ サービスの起動確認

## 🔧 次のステップ（必須）

### 1. 環境変数の設定

現在、基本的な環境変数（`OUTPUT_DIR=/tmp/outputs`）のみが設定されています。
以下の環境変数を追加してください：

#### 必須環境変数

```powershell
# 基本環境変数を設定（CORS_ORIGINSの*は特殊文字のため、後でGoogle Cloud Consoleから追加）
# 重要: YOUR_NEW_API_KEY_HERE を新しいGemini APIキーに置き換えてください
gcloud run services update helm-api `
  --region asia-northeast1 `
  --update-env-vars `
    "GOOGLE_API_KEY=YOUR_NEW_API_KEY_HERE,USE_LLM=true,GOOGLE_CLOUD_PROJECT_ID=helm-project-484105,CORS_ORIGINS=http://localhost:3000,OUTPUT_DIR=/tmp/outputs"
```

**注意**: `CORS_ORIGINS`に`https://*.vercel.app`を追加する場合は、Google Cloud Consoleから手動で設定してください：
1. [Cloud Run](https://console.cloud.google.com/run) ページにアクセス
2. `helm-api` サービスを選択
3. 「編集と新しいリビジョンをデプロイ」をクリック
4. 「変数とシークレット」タブで `CORS_ORIGINS` を編集
5. 値を `http://localhost:3000,https://*.vercel.app` に変更

**重要**:

- `your-api-key-here` を実際のGemini APIキーに置き換えてください
- APIキーは [Google AI Studio](https://makersuite.google.com/app/apikey) で取得できます

#### オプション環境変数（OAuth認証を使用する場合）

```powershell
gcloud run services update helm-api `
  --region asia-northeast1 `
  --update-env-vars `
    "GOOGLE_OAUTH_CREDENTIALS_FILE=/tmp/oauth-credentials.json,GOOGLE_DRIVE_FOLDER_ID=your-folder-id"
```

### 2. APIの動作確認

#### ヘルスチェック

```powershell
curl https://helm-api-dsy6lzllhq-an.a.run.app/
```

**期待される出力**:

```json
{"status":"ok","message":"Helm API is running"}
```

#### APIドキュメントの確認

ブラウザで以下のURLにアクセス：

```
https://helm-api-dsy6lzllhq-an.a.run.app/docs
```

FastAPIの自動生成ドキュメントが表示されることを確認してください。

#### 簡単なAPIテスト

```powershell
# 分析エンドポイントのテスト（モックデータが返される）
curl -X POST https://helm-api-dsy6lzllhq-an.a.run.app/api/analyze `
  -H "Content-Type: application/json" `
  -d '{"meeting_id": "test", "chat_id": "test"}'
```

### 3. ログの確認

```powershell
# 最新のログを確認
gcloud run services logs read helm-api --region asia-northeast1 --limit 50

# リアルタイムでログを監視
gcloud run services logs tail helm-api --region asia-northeast1
```

### 4. サービスの状態確認

```powershell
# サービスの詳細情報を確認
gcloud run services describe helm-api --region asia-northeast1

# サービスのURLを確認
gcloud run services describe helm-api --region asia-northeast1 --format="value(status.url)"
```

## 📝 環境変数の詳細

詳細な環境変数の説明は、[ENV_VARS_REFERENCE.md](./ENV_VARS_REFERENCE.md) を参照してください。

## 🔍 トラブルシューティング

問題が発生した場合は、[TROUBLESHOOTING.md](./TROUBLESHOOTING.md) を参照してください。

### よくある問題

1. **APIが応答しない**

   - 環境変数が正しく設定されているか確認
   - ログを確認してエラーがないか確認
2. **LLMが動作しない**

   - `GOOGLE_API_KEY` が正しく設定されているか確認
   - `USE_LLM=true` が設定されているか確認
3. **CORSエラー**

   - `CORS_ORIGINS` にフロントエンドのURLが含まれているか確認

## 🚀 フロントエンドとの連携

フロントエンド（Next.js）からこのAPIを使用する場合：

1. フロントエンドの環境変数に以下を設定：

   ```
   NEXT_PUBLIC_API_URL=https://helm-api-dsy6lzllhq-an.a.run.app
   ```
2. CORS設定を確認：

   - フロントエンドのURLが `CORS_ORIGINS` に含まれていることを確認

## 📚 参考ドキュメント

- [デプロイ後確認手順](./POST_DEPLOY_CHECK.md)
- [環境変数リファレンス](./ENV_VARS_REFERENCE.md)
- [手作業セットアップガイド](./MANUAL_SETUP_GUIDE.md)
- [トラブルシューティング](./TROUBLESHOOTING.md)

---

**おめでとうございます！デプロイが完了しました！** 🎉
