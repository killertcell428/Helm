# 環境変数の設定ガイド

## 重要な環境変数

Cloud RunでREACHAアプリケーションを動作させるには、以下の環境変数が必要です：

| 環境変数 | 説明 | 必須 |
|---------|------|------|
| `DIFY_API_KEY1` | Dify Chat APIキー（リサーチ実行用） | はい |
| `DIFY_API_KEY2` | Dify Workflow APIキー（提案作成用） | はい |
| `DIFY_USER_ID` | DifyユーザーID | いいえ（デフォルト: REACHA_agent） |
| `OUTPUTS_ROOT` | 出力ファイルの保存先 | いいえ（デフォルト: /tmp/outputs） |

## 初回設定

### 方法1: コマンドラインで設定（推奨）

```powershell
gcloud run services update reacha-app `
  --region asia-northeast1 `
  --update-env-vars `
    "DIFY_API_KEY1=your_key_1,DIFY_API_KEY2=your_key_2,DIFY_USER_ID=REACHA_agent,OUTPUTS_ROOT=/tmp/outputs"
```

**重要**: 複数の環境変数を設定する場合は、**カンマで区切って1行で指定**してください。

### 方法2: 個別に設定

```powershell
# DIFY_API_KEY1を設定
gcloud run services update reacha-app `
  --region asia-northeast1 `
  --update-env-vars DIFY_API_KEY1=your_key_1

# DIFY_API_KEY2を設定
gcloud run services update reacha-app `
  --region asia-northeast1 `
  --update-env-vars DIFY_API_KEY2=your_key_2

# DIFY_USER_IDを設定
gcloud run services update reacha-app `
  --region asia-northeast1 `
  --update-env-vars DIFY_USER_ID=REACHA_agent

# OUTPUTS_ROOTを設定
gcloud run services update reacha-app `
  --region asia-northeast1 `
  --update-env-vars OUTPUTS_ROOT=/tmp/outputs
```

## 環境変数の確認

```powershell
# すべての環境変数を確認
gcloud run services describe reacha-app `
  --region asia-northeast1 `
  --format="yaml(spec.template.spec.containers[0].env)"
```

## 環境変数の保持

**重要なポイント**: 環境変数は一度設定すれば、次回のデプロイ時にも**自動的に保持**されます。

- `deploy.ps1` を実行しても、既存の環境変数は上書きされません
- 新しい環境変数を追加する場合は、`--update-env-vars` で明示的に指定する必要があります
- 既存の環境変数を変更する場合も、`--update-env-vars` で更新してください

## デプロイスクリプトとの関係

`deploy.ps1` は以下の環境変数のみを設定します：

- `OUTPUTS_ROOT=/tmp/outputs`

`DIFY_API_KEY1` と `DIFY_API_KEY2` は、**初回のみ手動で設定**する必要があります。設定後は、デプロイ時に自動的に保持されます。

## トラブルシューティング

### 環境変数が正しく設定されていない

1. **設定を確認**
   ```powershell
   gcloud run services describe reacha-app `
     --region asia-northeast1 `
     --format="get(spec.template.spec.containers[0].env)"
   ```

2. **再設定**
   ```powershell
   gcloud run services update reacha-app `
     --region asia-northeast1 `
     --update-env-vars "DIFY_API_KEY1=your_key_1,DIFY_API_KEY2=your_key_2"
   ```

### Dify APIが動作しない

1. **ログを確認**
   ```powershell
   gcloud run services logs read reacha-app `
     --region asia-northeast1 `
     --limit 50 `
     | Select-String "DIFY|API"
   ```

2. **環境変数が設定されているか確認**
   - 上記の「環境変数の確認」コマンドを実行

3. **APIキーが正しいか確認**
   - DifyのダッシュボードでAPIキーを確認

## Secret Managerの使用（推奨）

機密情報はSecret Managerを使用することを推奨します：

```powershell
# Secret Managerにシークレットを保存
echo -n "your_api_key" | gcloud secrets create dify-api-key-1 --data-file=-

# Cloud Runでシークレットを使用
gcloud run services update reacha-app `
  --region asia-northeast1 `
  --update-secrets DIFY_API_KEY1=dify-api-key-1:latest
```

## 参考

- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - デプロイ手順の詳細
- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager/docs)

