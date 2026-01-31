# APIテスト結果と確認方法

## ✅ テスト結果

### 1. ヘルスチェック（成功）

```powershell
Invoke-WebRequest -Uri "https://helm-api-dsy6lzllhq-an.a.run.app/" -Method GET -UseBasicParsing | Select-Object -ExpandProperty Content
```

**結果**: ✅ 成功
```json
{"message":"Helm API","version":"0.1.0","status":"running"}
```

**意味**: APIは正常に起動しており、リクエストを受け付けています。

### 2. 分析エンドポイント（エラー - これは正常）

```powershell
$body = @{
    meeting_id = "test-meeting-123"
    chat_id = "test-chat-456"
} | ConvertTo-Json

Invoke-WebRequest -Uri "https://helm-api-dsy6lzllhq-an.a.run.app/api/analyze" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing | Select-Object -ExpandProperty Content
```

**結果**: ⚠️ エラー（これは正常な動作）
```json
{
  "error_id": "c1616208-2291-488d-b83f-40251303a4ce",
  "error_code": "NOT_FOUND",
  "message": "会議データが見つかりません: test-meeting-123",
  "details": {
    "resource_type": "meeting",
    "resource_id": "test-meeting-123"
  }
}
```

**意味**: 
- APIは正常に動作しています
- `test-meeting-123`というIDの会議データが存在しないため、適切にエラーを返しています
- これは期待通りの動作です

## 🔧 セキュリティ警告の回避

PowerShellのセキュリティ警告を回避するには、`-UseBasicParsing`オプションを追加してください：

```powershell
Invoke-WebRequest -Uri "https://helm-api-dsy6lzllhq-an.a.run.app/" -Method GET -UseBasicParsing
```

## 🧪 実際のデータでテストする方法

### 方法1: 実際のGoogle Meet/Chatデータを使用

実際のGoogle Meet会議IDとChat IDを使用してテストします。

```powershell
$body = @{
    meeting_id = "実際の会議ID"
    chat_id = "実際のチャットID"
} | ConvertTo-Json

Invoke-WebRequest -Uri "https://helm-api-dsy6lzllhq-an.a.run.app/api/analyze" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing | Select-Object -ExpandProperty Content
```

### 方法2: モックデータを使用（開発環境）

開発環境では、モックデータが自動的に返される場合があります。エンドポイントによっては、存在しないIDでもモックデータを返すことがあります。

### 方法3: 他のエンドポイントをテスト

存在チェックが不要なエンドポイントをテストします：

```powershell
# ヘルスチェック（既に成功確認済み）
Invoke-WebRequest -Uri "https://helm-api-dsy6lzllhq-an.a.run.app/" -Method GET -UseBasicParsing | Select-Object -ExpandProperty Content
```

## 📊 エラーレスポンスの確認

エラーレスポンスが返された場合でも、APIは正常に動作しています。エラーの内容を確認するには：

```powershell
try {
    $response = Invoke-WebRequest -Uri "https://helm-api-dsy6lzllhq-an.a.run.app/api/analyze" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    $response.Content
} catch {
    $_.Exception.Response.StatusCode
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $reader.BaseStream.Position = 0
    $reader.DiscardBufferedData()
    $responseBody = $reader.ReadToEnd()
    $responseBody | ConvertFrom-Json | ConvertTo-Json -Depth 10
}
```

## ✅ 確認完了項目

- [x] APIが起動している（ヘルスチェック成功）
- [x] エラーハンドリングが正常に動作している
- [x] レスポンスがJSON形式で返されている
- [x] エラーメッセージが適切に返されている

## 🚀 次のステップ

1. **フロントエンドとの連携**
   - フロントエンドからAPIを呼び出す
   - CORS設定の確認

2. **実際のデータでのテスト**
   - 実際のGoogle Meet/Chatデータでテスト
   - LLM統合の動作確認

3. **ログの確認**
   ```powershell
   gcloud run services logs read helm-api --region asia-northeast1 --limit 50
   ```

---

**APIは正常に動作しています！** 🎉
