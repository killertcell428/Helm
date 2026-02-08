# 環境変数リファレンス

Helm Backend APIで使用するすべての環境変数の詳細説明です。

## 目次

1. [必須環境変数](#必須環境変数)
2. [認証関連環境変数](#認証関連環境変数)
3. [LLM統合環境変数](#llm統合環境変数)
4. [API設定環境変数](#api設定環境変数)
5. [CORS設定環境変数](#cors設定環境変数)
6. [タイムアウト設定環境変数](#タイムアウト設定環境変数)
7. [リトライ設定環境変数](#リトライ設定環境変数)
8. [エスカレーション設定環境変数](#エスカレーション設定環境変数)
9. [その他の環境変数](#その他の環境変数)

---

## 必須環境変数

### `GOOGLE_API_KEY`

**説明**: Gemini APIキー（ADK用、Gemini API用）

**必須**: はい（LLM統合を使用する場合）

**取得方法**: [Google AI Studio](https://makersuite.google.com/app/apikey) で取得

**例**:
```bash
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**注意**: 
- APIキーは機密情報です。漏洩しないよう注意してください
- Cloud Runでは環境変数またはSecret Managerを使用してください

---

### `USE_LLM`

**説明**: LLM統合を有効化するかどうか

**必須**: はい（LLM統合を使用する場合）

**デフォルト値**: `false`

**有効な値**: `true`, `false`

**例**:
```bash
USE_LLM=true
```

**注意**: 
- `true` に設定すると、実際のLLM（Gemini）が使用されます
- `false` の場合は、モックデータが使用されます

---

### `GOOGLE_CLOUD_PROJECT_ID`

**説明**: Google Cloud Project ID

**必須**: はい（LLM統合を使用する場合）

**デフォルト値**: なし

**例**:
```bash
GOOGLE_CLOUD_PROJECT_ID=helm-project-484105
```

**注意**: 
- 既存のプロジェクトIDを使用してください

---

## 認証関連環境変数

### `GOOGLE_OAUTH_CREDENTIALS_FILE`

**説明**: OAuth 2.0 クライアントIDのJSONファイルパス

**必須**: いいえ（OAuth認証を使用する場合のみ）

**デフォルト値**: なし

**例**:
```bash
# ローカル開発時
GOOGLE_OAUTH_CREDENTIALS_FILE=./credentials/oauth-credentials.json

# Cloud Run（Secret Manager使用時）
GOOGLE_OAUTH_CREDENTIALS_FILE=/tmp/oauth-credentials.json
```

**注意**: 
- OAuth認証を使用する場合に必要です
- Cloud RunではSecret Managerを使用することを推奨します
- JSONファイルには機密情報が含まれています

---

### `GOOGLE_OAUTH_CLIENT_ID`

**説明**: OAuth 2.0 クライアントID

**必須**: いいえ（`GOOGLE_OAUTH_CREDENTIALS_FILE`がない場合）

**デフォルト値**: なし

**例**:
```bash
GOOGLE_OAUTH_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
```

**注意**: 
- `GOOGLE_OAUTH_CREDENTIALS_FILE` が設定されている場合は不要です

---

### `GOOGLE_OAUTH_CLIENT_SECRET`

**説明**: OAuth 2.0 クライアントシークレット

**必須**: いいえ（`GOOGLE_OAUTH_CREDENTIALS_FILE`がない場合）

**デフォルト値**: なし

**例**:
```bash
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
```

**注意**: 
- `GOOGLE_OAUTH_CREDENTIALS_FILE` が設定されている場合は不要です
- 機密情報です。漏洩しないよう注意してください

---

### `GOOGLE_DRIVE_FOLDER_ID`

**説明**: Google DriveフォルダID（個人フォルダ使用時）

**必須**: いいえ（OAuth認証を使用する場合のみ）

**デフォルト値**: なし

**例**:
```bash
GOOGLE_DRIVE_FOLDER_ID=1a2b3c4d5e6f7g8h9i0j
```

**取得方法**: 
- Google Driveでフォルダを作成または選択
- フォルダのURLからIDを取得
- 例: `https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j` → ID: `1a2b3c4d5e6f7g8h9i0j`

---

### `GOOGLE_APPLICATION_CREDENTIALS`

**説明**: サービスアカウントの認証情報JSONファイルパス

**必須**: いいえ（サービスアカウントを使用する場合のみ）

**デフォルト値**: なし

**例**:
```bash
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account-key.json
```

**注意**: 
- サービスアカウントを使用する場合に必要です
- OAuth認証を使用する場合は設定しないでください

---

### `GOOGLE_DRIVE_SHARED_DRIVE_ID`

**説明**: 共有ドライブID（サービスアカウント使用時は必須）

**必須**: いいえ（サービスアカウントを使用する場合のみ）

**デフォルト値**: なし

**例**:
```bash
GOOGLE_DRIVE_SHARED_DRIVE_ID=0a1b2c3d4e5f6g7h8i9j
```

---

## LLM統合環境変数

### `LLM_MODEL`

**説明**: 使用するLLMモデル

**必須**: いいえ

**デフォルト値**: `gemini-1.5-flash`

**有効な値**: 
- `gemini-1.5-flash` (推奨: 高速でコスト効率が良い)
- `gemini-1.5-pro` (推奨: より高精度)
- `gemini-1.5-flash-002` (最新版)
- `gemini-1.5-pro-002` (最新版)

**注意**: 
- `gemini-2.0-flash-001` は廃止予定のため使用しないでください
- `gemini-pro` はレガシーモデルのため、`gemini-1.5-pro` を使用してください

**例**:
```bash
LLM_MODEL=gemini-1.5-flash
```

---

### `LLM_MAX_RETRIES`

**説明**: LLM API呼び出しの最大リトライ回数

**必須**: いいえ

**デフォルト値**: `3`

**例**:
```bash
LLM_MAX_RETRIES=3
```

---

### `LLM_TIMEOUT`

**説明**: LLM API呼び出しのタイムアウト時間（秒）

**必須**: いいえ

**デフォルト値**: `60`

**例**:
```bash
LLM_TIMEOUT=300
```

---

### `LLM_TEMPERATURE`

**説明**: LLMの温度パラメータ（0.0-1.0）

**必須**: いいえ

**デフォルト値**: `0.2`

**例**:
```bash
LLM_TEMPERATURE=0.2
```

**注意**: 
- 値が低いほど、より確定的な回答を生成します
- 値が高いほど、より創造的な回答を生成します

---

### `LLM_TOP_P`

**説明**: LLMのTop-pサンプリングパラメータ（0.0-1.0）

**必須**: いいえ

**デフォルト値**: `0.95`

**例**:
```bash
LLM_TOP_P=0.95
```

---

## API設定環境変数

### `API_TITLE`

**説明**: APIのタイトル

**必須**: いいえ

**デフォルト値**: `Helm API`

**例**:
```bash
API_TITLE=Helm API
```

---

### `API_VERSION`

**説明**: APIのバージョン

**必須**: いいえ

**デフォルト値**: `0.1.0`

**例**:
```bash
API_VERSION=0.1.0
```

---

## CORS設定環境変数

### `CORS_ORIGINS`

**説明**: CORS許可オリジン（カンマ区切り）

**必須**: いいえ

**デフォルト値**: `http://localhost:3000,https://*.vercel.app`

**例**:
```bash
CORS_ORIGINS=http://localhost:3000,https://*.vercel.app,https://your-frontend-domain.com
```

**注意**: 
- フロントエンドのURLを追加してください
- ワイルドカード（`*`）を使用できます

---

## タイムアウト設定環境変数

### `DEFAULT_TIMEOUT`

**説明**: デフォルトのタイムアウト時間（秒）

**必須**: いいえ

**デフォルト値**: `60`

**例**:
```bash
DEFAULT_TIMEOUT=60
```

---

### `LLM_TIMEOUT`

**説明**: LLM処理のタイムアウト時間（秒）

**必須**: いいえ

**デフォルト値**: `300`（5分）

**例**:
```bash
LLM_TIMEOUT=300
```

---

### `EXECUTION_TIMEOUT`

**説明**: 実行処理のタイムアウト時間（秒）

**必須**: いいえ

**デフォルト値**: `600`（10分）

**例**:
```bash
EXECUTION_TIMEOUT=600
```

---

## リトライ設定環境変数

### `MAX_RETRIES`

**説明**: 最大リトライ回数

**必須**: いいえ

**デフォルト値**: `3`

**例**:
```bash
MAX_RETRIES=3
```

---

### `RETRY_BACKOFF_BASE`

**説明**: リトライのバックオフベース（指数バックオフ）

**必須**: いいえ

**デフォルト値**: `2.0`

**例**:
```bash
RETRY_BACKOFF_BASE=2.0
```

---

### `RETRY_INITIAL_DELAY`

**説明**: リトライの初期遅延時間（秒）

**必須**: いいえ

**デフォルト値**: `1.0`

**例**:
```bash
RETRY_INITIAL_DELAY=1.0
```

---

## エスカレーション設定環境変数

### `ESCALATION_THRESHOLD`

**説明**: エスカレーション閾値（スコア）

**必須**: いいえ

**デフォルト値**: `70`

**例**:
```bash
ESCALATION_THRESHOLD=70
```

**注意**: 
- スコアがこの値以上の場合、エスカレーションが発生します

---

### `DEMO_MODE`

**説明**: デモモード（findingsがあれば常にエスカレーション）

**必須**: いいえ

**デフォルト値**: `true`

**有効な値**: `true`, `false`

**例**:
```bash
DEMO_MODE=true
```

---

## その他の環境変数

### `OUTPUT_DIR`

**説明**: 出力ファイルの保存ディレクトリ

**必須**: いいえ

**デフォルト値**: `outputs`

**例**:
```bash
# ローカル開発時
OUTPUT_DIR=outputs

# Cloud Run
OUTPUT_DIR=/tmp/outputs
```

**注意**: 
- Cloud Runでは `/tmp` ディレクトリを使用してください
- `/tmp` のデータはコンテナ再起動時に削除されます

---

### `LOG_LEVEL`

**説明**: ログレベル

**必須**: いいえ

**デフォルト値**: `INFO`

**有効な値**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**例**:
```bash
LOG_LEVEL=INFO
```

---

### `ENABLE_FILE_LOGGING`

**説明**: ファイルロギングを有効化するかどうか

**必須**: いいえ

**デフォルト値**: `false`

**有効な値**: `true`, `false`

**例**:
```bash
ENABLE_FILE_LOGGING=false
```

**注意**: Cloud Run では標準出力が Cloud Logging に送られるため、通常は `false` のままで問題ありません。

---

### `LOG_FORMAT`

**説明**: ログ出力形式。`json` にすると Cloud Logging で request_id や endpoint による検索がしやすくなります。

**必須**: いいえ

**デフォルト値**: `text`

**有効な値**: `text`, `json`

**例**:
```bash
# Cloud Run 推奨
LOG_FORMAT=json
```

**参考**: [ログとモニタリング](./LOGGING_AND_MONITORING.md)

---

### `ERROR_NOTIFICATION_ENABLED`

**説明**: エラー発生時にファイル（`logs/error_notifications.json`）へ記録するかどうか。

**必須**: いいえ

**デフォルト値**: `true`（ただし Cloud Run など書き込み不可の環境では自動で無効になります）

**有効な値**: `true`, `false`

**例**:
```bash
ERROR_NOTIFICATION_ENABLED=false
```

---

## Cloud Runでの環境変数設定方法

### 方法1: コマンドラインで設定

```powershell
gcloud run services update helm-api `
  --region asia-northeast1 `
  --update-env-vars `
    "GOOGLE_API_KEY=your-key,USE_LLM=true,GOOGLE_CLOUD_PROJECT_ID=helm-project-484105"
```

### 方法2: Google Cloud Consoleから設定

1. [Cloud Run](https://console.cloud.google.com/run) ページにアクセス
2. `helm-api` サービスを選択
3. 「編集と新しいリビジョンをデプロイ」をクリック
4. 「変数とシークレット」タブを選択
5. 「変数を追加」をクリックして環境変数を追加

### 方法3: Secret Managerを使用（推奨、機密情報の場合）

```powershell
# Secret Managerにシークレットを保存
echo -n "your-api-key" | gcloud secrets create google-api-key --data-file=-

# Cloud Runでシークレットを使用
gcloud run services update helm-api `
  --region asia-northeast1 `
  --update-secrets GOOGLE_API_KEY=google-api-key:latest
```

---

## 環境変数の確認方法

### すべての環境変数を確認

```powershell
gcloud run services describe helm-api `
  --region asia-northeast1 `
  --format="yaml(spec.template.spec.containers[0].env)"
```

### 特定の環境変数を確認

```powershell
gcloud run services describe helm-api `
  --region asia-northeast1 `
  --format="get(spec.template.spec.containers[0].env)" | Select-String "GOOGLE_API_KEY"
```

---

## 参考

- [手作業セットアップガイド](./MANUAL_SETUP_GUIDE.md)
- [デプロイ前チェックリスト](./DEPLOY_CHECKLIST.md)
- [トラブルシューティング](./TROUBLESHOOTING.md)
