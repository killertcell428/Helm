# CORSエラー修正ガイド

**エラー**: 
```
Access to fetch at 'https://helm-api-dsy6lzllhq-an.a.run.app/api/meetings/ingest' 
from origin 'https://v0-helm-pdca-demo.vercel.app' has been blocked by CORS policy
```

## 🔧 解決方法：Google Cloud ConsoleからCORS設定を更新

### ステップ1: Cloud Runコンソールにアクセス

1. [Cloud Run](https://console.cloud.google.com/run?project=helm-project-484105) にアクセス
2. プロジェクト `helm-project-484105` が選択されていることを確認
3. `helm-api` サービスをクリック

### ステップ2: サービスを編集

1. 上部の **「編集と新しいリビジョンをデプロイ」** ボタンをクリック

### ステップ3: 環境変数を更新

1. **「変数とシークレット」** タブをクリック
2. **「変数」** セクションで `CORS_ORIGINS` を探す
3. `CORS_ORIGINS` の **「編集」** ボタン（鉛筆アイコン）をクリック
4. **値** を以下に変更：
   ```
   http://localhost:3000,https://v0-helm-pdca-demo.vercel.app
   ```
5. **「保存」** をクリック

### ステップ4: デプロイ

1. ページ下部の **「デプロイ」** ボタンをクリック
2. デプロイが完了するまで待機（約1-2分）

### ステップ5: 動作確認

1. フロントエンド（https://v0-helm-pdca-demo.vercel.app）にアクセス
2. ブラウザの開発者ツール（F12）で **Console** タブを確認
3. CORSエラーが解消されていることを確認

## 📝 現在の設定

- **現在**: `CORS_ORIGINS=http://localhost:3000`
- **更新後**: `CORS_ORIGINS=http://localhost:3000,https://v0-helm-pdca-demo.vercel.app`

## ⚠️ その他のエラーについて

### Vercel Web Analytics エラー

```
GET https://v0-helm-pdca-demo.vercel.app/_vercel/insights/script.js net::ERR_BLOCKED_BY_CLIENT
```

**説明**: これは広告ブロッカーやプライバシー拡張機能がブロックしている可能性があります。アプリの機能には影響しません。

**対処**: 無視して問題ありません。

### 画像のpreload警告

```
The resource https://v0-helm-pdca-demo.vercel.app/helm-logo-light.png was preloaded using link preload but not used within a few seconds
```

**説明**: 画像のpreloadに関する警告です。アプリの機能には影響しません。

**対処**: 無視して問題ありません。

## ✅ 確認チェックリスト

- [ ] Cloud Runコンソールで `CORS_ORIGINS` を更新
- [ ] デプロイが完了
- [ ] フロントエンドでCORSエラーが解消されている
- [ ] APIリクエストが正常に送信されている

---

**CORS設定を更新したら、フロントエンドで再度テストしてください！** 🚀
