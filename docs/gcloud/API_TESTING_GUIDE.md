# API動作確認ガイド

FastAPIの自動生成ドキュメント（Swagger UI）の使い方を説明します。

## 📖 FastAPI自動生成ドキュメントの使い方

### 1. ドキュメントページにアクセス

ブラウザで以下のURLにアクセス：
```
https://helm-api-dsy6lzllhq-an.a.run.app/docs
```

### 2. ドキュメント画面の見方

#### 画面の構成

1. **上部**: APIのタイトルとバージョン情報
2. **左側**: エンドポイントの一覧
   - `/` - ヘルスチェック
   - `/api/analyze` - 構造的問題分析
   - `/api/escalate` - エスカレーション
   - `/api/approve` - 承認
   - `/api/execute` - 実行
   - など

3. **右側**: エンドポイントの詳細情報

### 3. APIをテストする方法

#### ステップ1: エンドポイントを選択

左側のリストからテストしたいエンドポイントをクリックします。
例：`GET /` （ヘルスチェック）

#### ステップ2: "Try it out" ボタンをクリック

エンドポイントの詳細画面で、右上の **"Try it out"** ボタンをクリックします。

#### ステップ3: パラメータを入力（必要な場合）

エンドポイントによっては、リクエストボディやパラメータの入力が必要です。

例：`POST /api/analyze` の場合：
```json
{
  "meeting_id": "test-meeting-123",
  "chat_id": "test-chat-456"
}
```

#### ステップ4: "Execute" ボタンをクリック

入力が完了したら、**"Execute"** ボタンをクリックします。

#### ステップ5: レスポンスを確認

画面下部に以下の情報が表示されます：
- **Request URL**: 実際に送信されたURL
- **Response Code**: HTTPステータスコード（200 = 成功）
- **Response Body**: APIからのレスポンス（JSON形式）

## 🧪 簡単なテスト例

### 1. ヘルスチェック（最も簡単）

1. `GET /` をクリック
2. "Try it out" をクリック
3. "Execute" をクリック

**期待されるレスポンス**:
```json
{
  "status": "ok",
  "message": "Helm API is running"
}
```

### 2. 構造的問題分析のテスト

1. `POST /api/analyze` をクリック
2. "Try it out" をクリック
3. Request bodyに以下を入力：
```json
{
  "meeting_id": "test-meeting-123",
  "chat_id": "test-chat-456"
}
```
4. "Execute" をクリック

**期待されるレスポンス**:
```json
{
  "analysis_id": "...",
  "status": "completed",
  "result": {
    "findings": [...],
    "overall_score": 75,
    ...
  }
}
```

## 🔍 よくある質問

### Q: "Try it out" ボタンが見つからない

A: エンドポイントをクリックして詳細を開くと表示されます。画面を下にスクロールしてください。

### Q: エラーが表示される

A: 以下の点を確認してください：
- リクエストボディの形式が正しいか（JSON形式）
- 必須パラメータがすべて入力されているか
- ログを確認してエラーの詳細を確認

### Q: レスポンスが返ってこない

A: タイムアウトの可能性があります。ログを確認してください：
```powershell
gcloud run services logs read helm-api --region asia-northeast1 --limit 50
```

## 📊 代替の確認方法（コマンドライン）

ブラウザが使えない場合や、自動化したい場合は、コマンドラインからもテストできます：

### PowerShellでテスト

```powershell
# ヘルスチェック（-UseBasicParsingでセキュリティ警告を回避）
Invoke-WebRequest -Uri "https://helm-api-dsy6lzllhq-an.a.run.app/" -Method GET -UseBasicParsing | Select-Object -ExpandProperty Content

# 分析エンドポイントのテスト
$body = @{
    meeting_id = "test-meeting-123"
    chat_id = "test-chat-456"
} | ConvertTo-Json

Invoke-WebRequest -Uri "https://helm-api-dsy6lzllhq-an.a.run.app/api/analyze" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing | Select-Object -ExpandProperty Content
```

**注意**: 
- `-UseBasicParsing`オプションを追加することで、PowerShellのセキュリティ警告を回避できます
- テストデータ（`test-meeting-123`）が存在しない場合は、エラーが返されますが、これは正常な動作です
- 実際の会議IDとチャットIDを使用するか、モックデータが有効なエンドポイントをテストしてください

### curlでテスト（Git BashやWSLを使用する場合）

```bash
# ヘルスチェック
curl https://helm-api-dsy6lzllhq-an.a.run.app/

# 分析エンドポイントのテスト
curl -X POST https://helm-api-dsy6lzllhq-an.a.run.app/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"meeting_id": "test-meeting-123", "chat_id": "test-chat-456"}'
```

## 🎯 次のステップ

APIが正常に動作することを確認したら：

1. **フロントエンドとの連携**
   - フロントエンドの環境変数に `NEXT_PUBLIC_API_URL` を設定
   - CORS設定を確認

2. **ログの監視**
   - リアルタイムログの確認方法を覚える
   - エラーが発生した場合の対処法を確認

3. **本番環境でのテスト**
   - 実際のGoogle Meet/Chatデータでテスト
   - LLM統合の動作確認

---

**APIの動作確認が完了したら、次のステップに進みましょう！** 🚀
