# 開発環境のoutputs同期について

## 概要

デプロイ時に、開発環境で生成された `back/outputs/` の内容がCloud Runでも参照できるようになります。

## 動作仕様

### デプロイ時

1. **Dockerイメージビルド時**
   - 開発環境の `back/outputs/` がDockerイメージに含まれます
   - イメージ内のパス: `/app/back/outputs/`

2. **Cloud Run起動時（初回のみ）**
   - アプリケーション起動時に、イメージ内の `/app/back/outputs/` から `/tmp/outputs/` にコピーされます
   - 既に `/tmp/outputs/` にデータがある場合はコピーされません（初回のみ）

### デプロイ後

- **Cloud Run側**: 新しい実行結果は `/tmp/outputs/` に保存されます
- **開発環境**: 開発環境の `back/outputs/` の変更はCloud Runには反映されません
- **同期**: デプロイ後の開発環境の変更は反映されません（デプロイ時に一度だけコピー）

## 設定

### .dockerignoreの設定

`.dockerignore` で `back/outputs/` が除外されている場合、デプロイ時に含まれません。

現在の設定では、`back/outputs/` はコメントアウトされているため、デプロイ時に含まれます：

```dockerignore
# 出力ファイル（デプロイ時は含めるため、.dockerignoreから除外）
# back/outputs/  # デプロイ時に開発環境のoutputsを含めるためコメントアウト
```

### Dockerfileの設定

`Dockerfile` でoutputsをコピーします：

```dockerfile
# 開発環境のoutputsをコピー（デプロイ時の初期データとして）
COPY back/outputs/ /app/back/outputs/
```

### アプリケーションの初期化処理

`back/app/main.py` の `ensure_outputs_root()` 関数で、Cloud Run起動時に初期化処理が実行されます：

- `OUTPUTS_ROOT` が `/tmp/outputs` の場合
- `/tmp/outputs` が空の場合
- イメージ内の `/app/back/outputs/` からコピー

## 注意事項

### イメージサイズ

開発環境のoutputsが大きい場合、Dockerイメージのサイズが大きくなります。

- イメージサイズが大きいと、ビルド・プッシュ・デプロイに時間がかかります
- 必要に応じて、不要なoutputsを削除してからデプロイしてください

### 永続化

Cloud Runは一時的なストレージ（`/tmp`）のみ提供します。

- `/tmp/outputs` のデータは、コンテナ再起動時に削除される可能性があります
- 永続的なストレージが必要な場合は、Cloud Storageの使用を検討してください

### デプロイ後の更新

デプロイ後に開発環境で新しいoutputsを生成しても、Cloud Runには反映されません。

- 新しいoutputsを反映するには、再度デプロイする必要があります
- または、Cloud Storageを使用して手動で同期する方法もあります

## トラブルシューティング

### outputsが反映されない

1. **.dockerignoreの確認**
   ```bash
   # back/outputs/ がコメントアウトされているか確認
   cat .dockerignore | grep outputs
   ```

2. **Dockerイメージの確認**
   ```bash
   # イメージ内にoutputsが含まれているか確認
   docker run --rm gcr.io/PROJECT_ID/reacha-app:latest ls -la /app/back/outputs/
   ```

3. **ログの確認**
   ```bash
   # Cloud Runのログで初期化メッセージを確認
   gcloud run services logs read reacha-app --region asia-northeast1 | grep "Initialized outputs"
   ```

### イメージサイズが大きい

1. **不要なoutputsを削除**
   ```powershell
   # 特定の会社のoutputsを削除
   Remove-Item -Recurse -Force back\outputs\CompanyName
   ```

2. **.dockerignoreで特定の会社を除外**
   ```dockerignore
   back/outputs/CompanyName/
   ```

## 参考

- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - デプロイ手順の詳細
- [ARCHITECTURE_DESIGN.md](./ARCHITECTURE_DESIGN.md) - アーキテクチャの詳細
