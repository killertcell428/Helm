# LLM統合機能の状態確認方法

## 現在の状態を確認する方法

### 1. APIレスポンスで確認

#### 分析結果 (`/api/analyze`)

**レスポンスに以下のフィールドが追加されました**:

```json
{
  "analysis_id": "...",
  "analysis_result": {
    ...
  },
  "is_llm_generated": false,  // ← false = モック, true = LLM生成
  "llm_status": "disabled",    // ← "disabled", "mock_fallback", "success"
  "llm_model": null            // ← LLM生成の場合はモデル名（例: "gemini-3.0-pro"）
}
```

**状態の意味**:
- `is_llm_generated: false` → **モックデータ**
- `is_llm_generated: true` → **実際のLLM生成データ**
- `llm_status: "disabled"` → LLM統合が無効
- `llm_status: "mock_fallback"` → LLM呼び出し失敗でモックにフォールバック
- `llm_status: "success"` → LLM生成成功

#### タスク生成結果 (`/api/execute`)

**レスポンスに以下のフィールドが追加されました**:

```json
{
  "execution_id": "...",
  "tasks": [...],
  "is_llm_generated": false,  // ← false = モック, true = LLM生成
  "llm_status": "disabled",    // ← "disabled", "mock_fallback", "success"
  "llm_model": null            // ← LLM生成の場合はモデル名
}
```

### 2. ログで確認

バックエンドのログで以下を確認：

#### モックモードの場合

```
⚠️ LLM統合が無効のため、モック分析結果を返します（USE_LLM=false または GOOGLE_CLOUD_PROJECT_ID未設定）
```

または

```
⚠️ LLM統合が無効のため、モックタスク生成結果を返します（USE_LLM=false または GOOGLE_CLOUD_PROJECT_ID未設定）
```

#### 実際のLLMが動作している場合

```
Vertex AI利用可能: project=xxx, model=gemini-3.0-pro
LLM API呼び出し成功: model=gemini-3.0-pro, elapsed=2.34s
✅ LLM分析完了（実際のLLM生成）: overall_score=75, model=gemini-3.0-pro
```

または

```
✅ LLMタスク生成完了（実際のLLM生成）: total_tasks=5, model=gemini-3.0-pro
```

### 3. 出力ファイルで確認

`backend/outputs/` ディレクトリに生成されるJSONファイルを確認：

**モックデータの場合**:
```json
{
  "analysis_id": "...",
  "result": {
    ...
    "_is_mock": true,
    "_llm_status": "disabled"
  }
}
```

**実際のLLM生成の場合**:
```json
{
  "analysis_id": "...",
  "result": {
    ...
    "_is_mock": false,
    "_llm_status": "success",
    "_llm_model": "gemini-3.0-pro"
  }
}
```

## 実際のLLMを有効化する方法

### ステップ1: 環境変数の設定

`.env` ファイルまたは環境変数に以下を追加：

```bash
USE_LLM=true
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### ステップ2: バックエンドの再起動

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### ステップ3: 動作確認

1. ログで「Vertex AI利用可能」が表示されることを確認
2. `/api/analyze` を呼び出して、レスポンスの `is_llm_generated: true` を確認
3. ログで「✅ LLM分析完了（実際のLLM生成）」が表示されることを確認

## 現在の状態の確認コマンド

### 環境変数の確認

```bash
# PowerShell
$env:USE_LLM
$env:GOOGLE_CLOUD_PROJECT_ID

# または .envファイルを確認
cat .env | grep USE_LLM
cat .env | grep GOOGLE_CLOUD_PROJECT_ID
```

### APIレスポンスの確認

```bash
# 分析結果を取得して確認
curl http://localhost:8000/api/analyze -X POST -H "Content-Type: application/json" -d '{"meeting_id": "test", "chat_id": "test"}' | jq '.is_llm_generated, .llm_status, .llm_model'
```

## まとめ

- ✅ **コードは完全に実装済み**
- ⚠️ **デフォルトではモックモードで動作**
- ✅ **APIレスポンスとログでモック/LLM生成を区別可能**
- 🔧 **USE_LLM=true で実際のLLMを有効化可能**
