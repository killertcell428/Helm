# ADK (Agent Development Kit) セットアップガイド

このドキュメントでは、ADKを使用したマルチエージェントシステムのセットアップ手順を説明します。

## 前提条件

- **Python 3.10以上**（ADKの要件）
- pip（Pythonパッケージ管理ツール）

## 1. ADKのインストール

```bash
pip install google-adk
```

**注意**: `google-generativeai`はレガシーなのでインストールしないでください。ADKが内部で`google-genai`を使用します。

## 2. APIキーの取得と設定

### Gemini APIキーの取得

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. 「Create API Key」をクリックしてAPIキーを生成
3. 生成されたAPIキーをコピー

### 環境変数の設定

以下のいずれかの環境変数にAPIキーを設定します：

- `GOOGLE_API_KEY`（推奨）
- `GEMINI_API_KEY`（代替）

#### Windowsの場合

```powershell
set GOOGLE_API_KEY=your-api-key-here
```

#### macOS/Linuxの場合

```bash
export GOOGLE_API_KEY=your-api-key-here
```

#### .envファイルを使用する場合

`.env`ファイルを作成または編集して、以下を追加：

```env
GOOGLE_API_KEY=your-api-key-here
```

## 3. Vertex AI使用時の設定（オプション）

Vertex AIを使用する場合は、以下の設定が必要です。

### 3.1 Google Cloudプロジェクトの設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクトを作成または選択
3. Vertex AI APIを有効化

### 3.2 環境変数の設定

以下の環境変数を設定します：

```env
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-project-id
LOCATION=us-central1
```

### 3.3 認証情報の設定

サービスアカウントを使用する場合：

1. サービスアカウントを作成
2. 認証情報JSONファイルをダウンロード
3. 環境変数 `GOOGLE_APPLICATION_CREDENTIALS` にパスを設定

```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
```

### 3.4 VertexAiSessionService使用時の注意事項

**重要**: `VertexAiSessionService`を使用する場合は、**Agent Engine ID**が必要です。

1. [Vertex AI Agent Builder](https://console.cloud.google.com/ai/agents) でAgent Engineを作成
2. Agent Engine IDを取得
3. 環境変数に設定（実装時に追加予定）

現時点では、`InMemorySessionService`を使用しています。`VertexAiSessionService`を使用する場合は、Phase2で実装予定です。

## 4. 動作確認

### 4.1 ADKのインストール確認

```bash
python -c "from google.adk.agents.llm_agent import Agent; print('ADK is installed')"
```

エラーが発生しない場合は、ADKが正しくインストールされています。

### 4.2 APIキーの確認

```bash
python -c "import os; print('API Key:', 'SET' if os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY') else 'NOT SET')"
```

### 4.3 エージェントの動作確認

#### 方法1: テストスクリプトを使用（推奨）

実際のAPI統合（Vertex AI Search、Google Drive、Google Chat/Gmail API）がなくても動作確認できます。

```bash
cd Dev/backend
python test_adk_agents.py
```

このスクリプトは以下を確認します：
- ADKのセットアップ状況
- APIキーの設定状況
- 各エージェント（ResearchAgent、AnalysisAgent、NotificationAgent）の動作
- SharedContextの動作

#### 方法2: バックエンドサーバーを起動してAPI経由でテスト

```bash
cd Dev/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

その後、Swagger UI（http://localhost:8000/docs）から`/api/execute`エンドポイントをテストしてください。

**注意**: 実際のAPI統合（Vertex AI Search、Google Drive、Google Chat/Gmail API）がなくても、モック実装で動作確認できます。

## 5. トラブルシューティング

### 5.1 importエラー

**エラー**: `ModuleNotFoundError: No module named 'google.adk'`

**解決方法**:
```bash
pip install google-adk
```

### 5.2 APIキー関連のエラー

**エラー**: `API key not found` または `Authentication failed`

**解決方法**:
1. 環境変数 `GOOGLE_API_KEY` または `GEMINI_API_KEY` が設定されているか確認
2. APIキーが正しいか確認
3. `.env`ファイルを使用している場合、`python-dotenv`がインストールされているか確認

### 5.3 Vertex AI使用時のエラー

**エラー**: `Vertex AI initialization failed`

**解決方法**:
1. `GOOGLE_CLOUD_PROJECT` 環境変数が設定されているか確認
2. Vertex AI APIが有効化されているか確認
3. 認証情報が正しく設定されているか確認

### 5.4 ADK未インストール時の動作

ADKがインストールされていない場合、システムは自動的にモックモードにフォールバックします。エラーログに警告が表示されますが、動作は継続します。

## 6. Phase 2: 実際のAPI統合（将来実装時）

### 6.1 Vertex AI Search APIのセットアップ

1. Vertex AI Search APIを有効化
2. データストアを作成
3. 認証情報を設定
4. `search_market_data`関数を実際のAPI呼び出しに置き換え

### 6.2 Google Drive APIのセットアップ

1. Google Drive APIを有効化
2. OAuth認証を設定
3. スコープを設定（`https://www.googleapis.com/auth/drive.readonly`など）
4. `fetch_internal_data`関数を実際のAPI呼び出しに置き換え

### 6.3 Google Chat / Gmail APIのセットアップ

1. Google Chat APIまたはGmail APIを有効化
2. OAuth認証を設定
3. スコープを設定
4. `send_notification`関数を実際のAPI呼び出しに置き換え（Phase2で実装）

## 7. 参考資料

- [ADK公式ドキュメント](https://google.github.io/adk-docs/)
- [ADK Python APIリファレンス](https://google.github.io/adk-docs/api-reference/python/)
- [Gemini API ドキュメント](https://ai.google.dev/gemini-api/docs)
- [Vertex AI ドキュメント](https://cloud.google.com/vertex-ai/docs)
