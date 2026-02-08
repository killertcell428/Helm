# ログとモニタリング

Cloud Run で動かしている Helm API のログ確認方法と、エラー追跡のポイントです。

## Cloud Run のログの見方

### 1. Google Cloud Console（ログエクスプローラ）

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクト `helm-project-484105` を選択
2. 左メニュー **「運用」→「ロギング」→「ログ エクスプローラ」**
3. リソースで **「Cloud Run リビジョン」** を選び、サービス名に `helm-api` を指定

### 2. よく使うフィルタ例

| 目的 | クエリ例 |
|------|----------|
| エラーのみ | `severity>=ERROR` |
| 特定リクエストの追跡 | `jsonPayload.request_id="<X-Request-IDの値>"` |
| 遅いリクエスト（1秒超） | `jsonPayload.extra_data.process_time!=""` または テキストで "Slow request" 検索 |
| 今日のログ | 時間範囲を「今日」に設定 |

### 3. レスポンスヘッダーの X-Request-ID

- 各リクエストに `X-Request-ID` が付与されます（UUID）
- フロントやクライアントでエラー時にこの値を控えておくと、ログエクスプローラで `jsonPayload.request_id` を検索して同じリクエストのログだけを追えます

## 環境変数（ログまわり）

| 変数 | 説明 | 推奨（Cloud Run） |
|------|------|-------------------|
| `LOG_LEVEL` | ログレベル（DEBUG/INFO/WARNING/ERROR/CRITICAL） | `INFO` |
| `LOG_FORMAT` | `json` にすると JSON 形式（Cloud Logging で検索しやすい） | `json` |
| `ENABLE_FILE_LOGGING` | ローカルでファイルにログを書くか | `false` |
| `ERROR_NOTIFICATION_ENABLED` | エラー時にファイルへ記録するか（Cloud Run では自動で無効） | 未設定で可 |

Cloud Run では **標準出力がそのまま Cloud Logging に送られる** ため、ファイルログは不要です。`LOG_FORMAT=json` にすると `request_id` や `endpoint` でフィルタしやすくなります。

## エラー発生時の確認手順

1. **ログエクスプローラ**で `severity>=ERROR` を指定
2. 該当ログの `jsonPayload` を開く
   - `request_id`: 同じリクエストの他のログを追うときのキー
   - `endpoint`, `method`: どの API で失敗したか
   - `exception` または `extra_data.traceback`: スタックトレース
3. 必要に応じて `request_id` で前後の INFO ログも確認（リクエスト開始・完了・処理時間）

## バックエンド側の仕様（参考）

- **リクエストごと**: 開始・完了・処理時間を INFO で出力
- **1秒超のリクエスト**: WARNING で "Slow request detected" を出力
- **例外時**: カスタム例外は `error_notification_manager` で記録（ファイルが書ける環境のみ）。未処理例外はミドルウェアで ERROR ログ＋再 raise
- **構造化ログ**: `LOG_FORMAT=json` 時は `timestamp`, `level`, `message`, `request_id`, `endpoint`, `method`, `exception` などを JSON で出力

## 関連ドキュメント

- [環境変数リファレンス](./ENV_VARS_REFERENCE.md) - `LOG_LEVEL`, `ENABLE_FILE_LOGGING` など
- [デプロイ前チェックリスト](./DEPLOY_STATUS_CHECK.md)
- [トラブルシューティング](./TROUBLESHOOTING.md)
