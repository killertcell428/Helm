# フロントエンド本番デプロイ確認ガイド

**最終更新**: 2025年1月31日  
**目標**: VercelにデプロイされたフロントエンドとCloud Run APIの連携確認

## 📋 確認項目チェックリスト

- [ ] Vercel環境変数の設定
- [ ] CORS設定の確認
- [ ] 本番環境での動作確認
- [ ] WebSocket接続の確認

## 🔧 ステップ1: Vercel環境変数の設定

### 1.1 Vercelダッシュボードにアクセス

1. [Vercel Dashboard](https://vercel.com/dashboard) にログイン
2. プロジェクト `v0-helm-pdca-demo` を選択
3. **Settings** → **Environment Variables** を開く

### 1.2 環境変数を追加

以下の環境変数を追加：

| 変数名 | 値 | 環境 |
|--------|-----|------|
| `NEXT_PUBLIC_API_URL` | `https://helm-api-dsy6lzllhq-an.a.run.app` | Production, Preview, Development |

**設定手順**:
1. **Add New** をクリック
2. **Name**: `NEXT_PUBLIC_API_URL`
3. **Value**: `https://helm-api-dsy6lzllhq-an.a.run.app`
4. **Environment**: すべての環境（Production, Preview, Development）を選択
5. **Save** をクリック

### 1.3 再デプロイ

環境変数を追加した後、**Deployments** タブから最新のデプロイを選択し、**Redeploy** をクリックして再デプロイします。

または、以下のコマンドで再デプロイ：

```bash
cd Dev/app/v0-helm-demo
vercel --prod
```

## 🔧 ステップ2: CORS設定の確認

### 2.1 現在のCORS設定を確認

```powershell
gcloud run services describe helm-api --region asia-northeast1 --format="value(spec.template.spec.containers[0].env)" | ForEach-Object { $_ -split ';' } | Select-String "CORS"
```

### 2.2 VercelのURLを確認

Vercelダッシュボードで、プロジェクトの **Settings** → **Domains** から本番URLを確認します。

通常は以下のような形式：
- `https://v0-helm-pdca-demo.vercel.app`
- またはカスタムドメイン

### 2.3 CORS設定を更新

VercelのURLを `CORS_ORIGINS` に追加します。

**方法1: Google Cloud Consoleから設定（推奨）**

1. [Cloud Run](https://console.cloud.google.com/run) ページにアクセス
2. `helm-api` サービスを選択
3. **編集と新しいリビジョンをデプロイ** をクリック
4. **変数とシークレット** タブを選択
5. `CORS_ORIGINS` を編集
6. 値を `http://localhost:3000,https://v0-helm-pdca-demo.vercel.app` に変更
   - 実際のVercel URLに置き換えてください
7. **デプロイ** をクリック

**方法2: コマンドラインから設定**

```powershell
# VercelのURLを確認してから実行
gcloud run services update helm-api `
  --region asia-northeast1 `
  --update-env-vars "CORS_ORIGINS=http://localhost:3000,https://v0-helm-pdca-demo.vercel.app"
```

**注意**: `*` が含まれる場合は、Google Cloud Consoleから手動で設定してください。

## 🧪 ステップ3: 本番環境での動作確認

### 3.1 フロントエンドにアクセス

Vercelの本番URLにアクセス：
```
https://v0-helm-pdca-demo.vercel.app
```

### 3.2 ブラウザの開発者ツールで確認

1. ブラウザの開発者ツールを開く（F12）
2. **Network** タブを開く
3. フロントエンドでAPIを呼び出す操作を実行
4. リクエストが `https://helm-api-dsy6lzllhq-an.a.run.app` に送信されているか確認

### 3.3 エラーの確認

**Console** タブでエラーがないか確認：
- CORSエラーが表示されないか
- API接続エラーが表示されないか

### 3.4 実際の動作確認

1. **Case1デモページ** にアクセス
2. パターンを選択
3. 「データ取得」をクリック
4. APIが正常に呼び出されることを確認

## 🔌 ステップ4: WebSocket接続の確認

### 4.1 WebSocket接続の確認

1. ブラウザの開発者ツールを開く
2. **Network** タブを開く
3. **WS** フィルターを選択
4. フロントエンドで実行を開始
5. WebSocket接続が確立されることを確認

### 4.2 WebSocket URLの確認

WebSocket接続は以下のURLに接続されるはずです：
```
wss://helm-api-dsy6lzllhq-an.a.run.app/ws/execution/{execution_id}
```

## 🐛 トラブルシューティング

### 問題1: CORSエラーが発生する

**症状**:
```
Access to fetch at 'https://helm-api-dsy6lzllhq-an.a.run.app/...' from origin 'https://v0-helm-pdca-demo.vercel.app' has been blocked by CORS policy
```

**解決方法**:
1. `CORS_ORIGINS` にVercelのURLが含まれているか確認
2. Google Cloud Consoleから `CORS_ORIGINS` を更新
3. Cloud Runサービスを再デプロイ

### 問題2: API接続エラー

**症状**:
```
Failed to fetch
NetworkError when attempting to fetch resource
```

**解決方法**:
1. `NEXT_PUBLIC_API_URL` が正しく設定されているか確認
2. Vercelで再デプロイ
3. ブラウザのキャッシュをクリア

### 問題3: WebSocket接続が失敗する

**症状**:
```
WebSocket connection failed
```

**解決方法**:
1. Cloud RunのWebSocketエンドポイントが正しく動作しているか確認
2. ファイアウォールやプロキシの設定を確認
3. ブラウザの開発者ツールでWebSocket接続の詳細を確認

### 問題4: 環境変数が反映されない

**解決方法**:
1. Vercelで再デプロイを実行
2. 環境変数が正しい環境（Production）に設定されているか確認
3. ビルドログで環境変数が読み込まれているか確認

## ✅ 確認完了チェックリスト

- [ ] Vercel環境変数 `NEXT_PUBLIC_API_URL` が設定されている
- [ ] Cloud Runの `CORS_ORIGINS` にVercelのURLが含まれている
- [ ] フロントエンドからAPIが正常に呼び出される
- [ ] WebSocket接続が正常に確立される
- [ ] エラーが発生しない
- [ ] デモが正常に動作する

## 📚 参考ドキュメント

- [DEPLOY_SUCCESS_NEXT_STEPS.md](./DEPLOY_SUCCESS_NEXT_STEPS.md) - デプロイ後の次のステップ
- [API_TESTING_GUIDE.md](./API_TESTING_GUIDE.md) - APIテストガイド
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables) - Vercel環境変数の公式ドキュメント

---

**フロントエンドの本番デプロイ確認が完了したら、投稿用コンテンツ作成に進みましょう！** 🚀
