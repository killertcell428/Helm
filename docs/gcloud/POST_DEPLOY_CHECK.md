# デプロイ後確認手順

Helm Backend APIのデプロイが完了したら、以下の手順で動作を確認してください。

## 1. サービスの状態確認

### サービスの一覧を確認

```powershell
gcloud run services list --region asia-northeast1
```

**期待される出力**:
```
SERVICE    REGION           URL
helm-api   asia-northeast1  https://helm-api-xxxxx.asia-northeast1.run.app
```

### サービスの詳細を確認

```powershell
gcloud run services describe helm-api --region asia-northeast1
```

**確認ポイント**:
- `status.conditions[0].status` が `True` であること
- `status.url` が表示されていること
- `spec.template.spec.containers[0].resources` が正しく設定されていること

## 2. 環境変数の確認

### 環境変数の一覧を確認

```powershell
gcloud run services describe helm-api `
  --region asia-northeast1 `
  --format="yaml(spec.template.spec.containers[0].env)"
```

**確認ポイント**:
- `GOOGLE_API_KEY` が設定されていること
- `USE_LLM=true` が設定されていること
- `GOOGLE_CLOUD_PROJECT_ID=helm-project-484105` が設定されていること
- その他必要な環境変数が設定されていること

### 環境変数の個別確認

```powershell
# 特定の環境変数を確認
gcloud run services describe helm-api `
  --region asia-northeast1 `
  --format="value(spec.template.spec.containers[0].env[0].name,spec.template.spec.containers[0].env[0].value)"
```

## 3. ログの確認

### 最近のログを確認

```powershell
gcloud run services logs read helm-api --region asia-northeast1 --limit 50
```

**確認ポイント**:
- エラーメッセージがないこと
- アプリケーションが正常に起動していること
- `INFO` レベルのログが表示されていること

### リアルタイムログの確認

```powershell
gcloud run services logs tail helm-api --region asia-northeast1
```

**Ctrl+C** で停止できます。

### エラーログのフィルタリング

```powershell
gcloud run services logs read helm-api `
  --region asia-northeast1 `
  --limit 100 `
  | Select-String "ERROR|WARNING|Exception"
```

## 4. APIエンドポイントの動作確認

### ヘルスチェック

```powershell
# PowerShell
Invoke-WebRequest -Uri "https://helm-api-xxxxx.asia-northeast1.run.app/" -Method GET

# または curl
curl https://helm-api-xxxxx.asia-northeast1.run.app/
```

**期待される出力**:
```json
{"status":"ok","message":"Helm API is running"}
```

### APIドキュメントの確認

ブラウザで以下のURLにアクセス:
```
https://helm-api-xxxxx.asia-northeast1.run.app/docs
```

**確認ポイント**:
- Swagger UIが表示されること
- すべてのエンドポイントが表示されること
- エンドポイントの説明が表示されること

### 主要エンドポイントのテスト

#### 1. 議事録取り込みエンドポイント

```powershell
$body = @{
    meeting_id = "test-meeting-001"
    transcript = "This is a test transcript."
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "https://helm-api-xxxxx.asia-northeast1.run.app/api/meetings/ingest" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

#### 2. 分析エンドポイント

```powershell
$body = @{
    meeting_id = "test-meeting-001"
    chat_id = "test-chat-001"
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "https://helm-api-xxxxx.asia-northeast1.run.app/api/analyze" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

## 5. フロントエンドからの接続確認

### CORS設定の確認

フロントエンドからAPIにアクセスできるか確認:

```javascript
// フロントエンドのコード例
fetch('https://helm-api-xxxxx.asia-northeast1.run.app/api/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    meeting_id: 'test',
    chat_id: 'test'
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

**確認ポイント**:
- CORSエラーが発生しないこと
- レスポンスが正常に返ってくること

### フロントエンドの環境変数設定

フロントエンドの `.env.local` または環境変数に以下を設定:

```env
NEXT_PUBLIC_API_URL=https://helm-api-xxxxx.asia-northeast1.run.app
```

## 6. パフォーマンスの確認

### レスポンス時間の確認

```powershell
Measure-Command {
    Invoke-WebRequest -Uri "https://helm-api-xxxxx.asia-northeast1.run.app/" -Method GET
}
```

**期待される値**:
- ヘルスチェック: 1秒以内
- 分析エンドポイント: 5-10秒（LLM処理含む）

### リソース使用量の確認

```powershell
gcloud run services describe helm-api `
  --region asia-northeast1 `
  --format="yaml(spec.template.spec.containers[0].resources)"
```

**確認ポイント**:
- メモリ: 2Gi
- CPU: 2

## 7. セキュリティの確認

### 認証設定の確認

```powershell
gcloud run services describe helm-api `
  --region asia-northeast1 `
  --format="value(spec.template.spec.serviceAccountName)"
```

**確認ポイント**:
- サービスアカウントが設定されていること（使用する場合）
- 認証設定が適切であること

### HTTPSの確認

```powershell
# HTTPSが有効であることを確認
curl -I https://helm-api-xxxxx.asia-northeast1.run.app/
```

**期待される出力**:
```
HTTP/2 200
```

## 8. エラーハンドリングの確認

### 存在しないエンドポイントへのアクセス

```powershell
Invoke-WebRequest -Uri "https://helm-api-xxxxx.asia-northeast1.run.app/api/nonexistent" -Method GET
```

**期待される動作**:
- 404エラーが返されること
- エラーメッセージが適切であること

### 不正なリクエストのテスト

```powershell
$body = @{
    invalid_field = "test"
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "https://helm-api-xxxxx.asia-northeast1.run.app/api/analyze" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**期待される動作**:
- 422エラー（Validation Error）が返されること
- エラーメッセージが適切であること

## 9. モニタリングの設定（オプション）

### Cloud Monitoringの確認

1. [Cloud Monitoring](https://console.cloud.google.com/monitoring) にアクセス
2. 「リソース」→「Cloud Run」を選択
3. `helm-api` サービスを選択
4. メトリクスを確認:
   - リクエスト数
   - レイテンシ
   - エラー率
   - CPU使用率
   - メモリ使用率

## 10. トラブルシューティング

問題が発生した場合:

1. **ログを確認**
   ```powershell
   gcloud run services logs read helm-api --region asia-northeast1 --limit 100
   ```

2. **環境変数を再確認**
   ```powershell
   gcloud run services describe helm-api --region asia-northeast1 --format="yaml(spec.template.spec.containers[0].env)"
   ```

3. **サービスの状態を確認**
   ```powershell
   gcloud run services describe helm-api --region asia-northeast1
   ```

4. **トラブルシューティングガイドを参照**
   - [トラブルシューティング](./TROUBLESHOOTING.md)

## 確認完了チェックリスト

- [ ] サービスの状態が正常
- [ ] 環境変数が正しく設定されている
- [ ] ログにエラーがない
- [ ] ヘルスチェックが成功
- [ ] APIドキュメントが表示される
- [ ] 主要エンドポイントが動作する
- [ ] フロントエンドから接続できる
- [ ] レスポンス時間が適切
- [ ] エラーハンドリングが適切

すべての項目が確認できたら、デプロイは成功です！

## 次のステップ

- [環境変数リファレンス](./ENV_VARS_REFERENCE.md) で詳細を確認
- [トラブルシューティング](./TROUBLESHOOTING.md) で問題を解決
- 定期的にログを確認して、問題がないか監視
