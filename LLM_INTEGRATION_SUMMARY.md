# LLM統合とタスク生成実装サマリー

**実装日**: 2025年1月12日

## 実装完了項目

### ✅ 1. プロンプト管理システムの構築

**ファイル**:
- `backend/services/prompts/__init__.py`
- `backend/services/prompts/analysis_prompt.py` - 分析用プロンプト
- `backend/services/prompts/task_generation_prompt.py` - タスク生成用プロンプト

**機能**:
- テンプレートベースのプロンプト生成
- 会議・チャット・会議資料をインプットに含める
- JSON形式の出力を指定
- 後からプロンプトエンジニアリングしやすい構造

### ✅ 2. 評価構造の設計

**ファイル**:
- `backend/services/evaluation/__init__.py`
- `backend/services/evaluation/schema.py` - 評価スキーマ定義（Pydanticモデル）
- `backend/services/evaluation/parser.py` - LLMレスポンスのパース

**機能**:
- 分析結果のスキーマ（findings, scores, explanation等）
- タスク定義のスキーマ（id, name, type, dependencies等）
- JSONレスポンスのパースとバリデーション
- エラーハンドリング（パース失敗時のフォールバック）

### ✅ 3. LLM統合サービスの実装

**ファイル**:
- `backend/services/llm_service.py`

**機能**:
- Vertex AI / Gemini APIの呼び出し（Gemini 3を優先使用）
- プロンプト管理システムとの連携
- レスポンスのパースとバリデーション
- エラーハンドリングとフォールバック（モックへのフォールバック）
- リトライロジック（指数バックオフ）
- JSON形式の強制（`response_mime_type="application/json"`）

**主要メソッド**:
- `analyze_structure(meeting_data, chat_data, materials_data)` - 構造的問題分析
- `generate_tasks(analysis_result, approval_data)` - タスク生成
- `_call_llm(prompt, response_format, model_name)` - LLM API呼び出し（内部）

### ✅ 4. 会議資料取り込みAPI

**ファイル**:
- `backend/main.py` - `/api/materials/ingest` エンドポイント追加

**機能**:
- リクエストスキーマ: `MaterialIngestRequest` (material_id, content, metadata)
- 会議資料データの保存（`materials_db`）
- エラーハンドリング

### ✅ 5. 分析結果生成のLLM統合

**ファイル**:
- `backend/main.py` - `/api/analyze` エンドポイント修正

**機能**:
- 会議・チャット・会議資料を取得
- LLMサービスを呼び出して分析
- 分析結果をJSON形式で保存（`outputs/analysis_{id}.json`）
- 既存のルールベース分析へのフォールバック

### ✅ 6. タスク生成のLLM統合

**ファイル**:
- `backend/main.py` - `/api/execute` エンドポイント修正

**機能**:
- 分析結果と承認データを取得
- LLMサービスを呼び出してタスクを生成
- 生成されたタスクを実行計画に反映
- タスク生成結果をJSON形式で保存（`outputs/tasks_{execution_id}.json`）
- 既存のハードコードされたタスクへのフォールバック

### ✅ 7. 出力ファイル生成機能

**ファイル**:
- `backend/services/output_service.py` - 出力サービス
- `backend/main.py` - `/api/outputs` と `/api/outputs/{file_id}` エンドポイント追加

**機能**:
- 分析結果のJSON出力（`outputs/analysis_{analysis_id}.json`）
- タスク定義のJSON出力（`outputs/tasks_{execution_id}.json`）
- ファイル保存（`outputs/` ディレクトリ）
- ファイル一覧取得API（`GET /api/outputs`）
- ファイルダウンロードAPI（`GET /api/outputs/{file_id}`）

### ✅ 8. 既存コードとの統合

**変更ファイル**:
- `backend/services/__init__.py` - LLMServiceを追加
- `backend/main.py` - LLMServiceとOutputServiceの初期化、各エンドポイントの修正
- `backend/config.py` - LLM関連の設定を追加

**機能**:
- 既存のVertex AIサービスとの共存（互換性維持）
- モックモードとの切り替え（環境変数ベース）
- エラーハンドリングの統一

## 環境変数設定

以下の環境変数を設定することで、LLM統合を有効化できます：

```bash
# LLM統合の有効化
USE_LLM=true

# 使用するモデル（デフォルト: gemini-3.0-pro）
LLM_MODEL=gemini-3.0-pro

# 最大リトライ回数（デフォルト: 3）
LLM_MAX_RETRIES=3

# タイムアウト時間（秒、デフォルト: 60）
LLM_TIMEOUT=60

# 温度パラメータ（デフォルト: 0.2）
LLM_TEMPERATURE=0.2

# Top-pサンプリング（デフォルト: 0.95）
LLM_TOP_P=0.95

# 出力ファイルの保存ディレクトリ（デフォルト: outputs/）
OUTPUT_DIR=outputs

# Google Cloud設定（必須）
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

## APIエンドポイント

### 新規追加

1. **`POST /api/materials/ingest`** - 会議資料の取り込み
2. **`GET /api/outputs`** - 出力ファイル一覧取得
3. **`GET /api/outputs/{file_id}`** - 出力ファイルダウンロード

### 修正

1. **`POST /api/analyze`** - LLM統合（material_idパラメータ追加）
2. **`POST /api/execute`** - LLM統合（タスク生成をLLMに委譲）

## データフロー

```
1. データ取り込み
   POST /api/meetings/ingest → meetings_db
   POST /api/chat/ingest → chats_db
   POST /api/materials/ingest → materials_db (新規)

2. 構造的問題分析
   POST /api/analyze
   → LLM Service.analyze_structure()
   → Prompt: analysis_prompt.py
   → LLM API (Vertex AI / Gemini)
   → Parser: evaluation/parser.py
   → JSON出力: outputs/analysis_{id}.json
   → analyses_db

3. Executive承認
   POST /api/approve → approvals_db

4. タスク生成
   POST /api/execute
   → LLM Service.generate_tasks()
   → Prompt: task_generation_prompt.py
   → LLM API (Vertex AI / Gemini)
   → Parser: evaluation/parser.py
   → JSON出力: outputs/tasks_{execution_id}.json
   → executions_db
```

## エラーハンドリング

1. **LLM API呼び出し失敗**: モック実装にフォールバック
2. **JSONパース失敗**: エラーログを出力し、モック実装にフォールバック
3. **タイムアウト**: リトライ（最大3回）後、フォールバック
4. **バリデーションエラー**: エラーメッセージを返し、ユーザーに通知

## コンペ要件との整合性

### ✅ 必須条件の満足

1. **Google Cloud アプリケーション実行プロダクト**: Cloud Runを使用（既に実装済み）
2. **Google Cloud AI技術**: Vertex AI / Gemini APIを使用（本実装で対応）

### ✅ 審査基準との整合性

1. **課題の新規性**: 「AIが人を呼び出す」「組織構造を改善対象として扱う」 ✅
2. **解決策の有効性**: 
   - 多様な情報源（会議・チャット・会議資料）からの統合評価 ✅
   - 定量評価パイプライン（スコア0-100点、説明可能な評価） ✅
3. **実装品質と拡張性**: 
   - プロンプト管理の分離（後から改修しやすい） ✅
   - 評価構造の設計（拡張可能） ✅
   - エラーハンドリングとフォールバック ✅

### 🚀 コンペで勝つための強化ポイント

1. **Gemini 3の活用**: 最新鋭モデルを明示的に使用（`gemini-3.0-pro`）
2. **プロンプトエンジニアリング**: 初期実装から始めるが、改善の余地を残す設計
3. **定量評価の精度**: スコアリングロジックの透明性と再現性
4. **出力ファイルの活用**: JSON出力のダウンロード機能と可視化
5. **デプロイの完全性**: バックエンド（Cloud Run）+ フロントエンド（Firebase Hosting or Vercel）

## 次のステップ

1. **動作確認**: 実際のLLM APIを呼び出して動作確認
2. **プロンプト改善**: 初期実装から始めて、Few-shot examplesやChain-of-Thought reasoningを追加
3. **評価構造の詳細化**: より詳細な評価項目の追加
4. **フロントエンド統合**: 出力ファイルの表示とダウンロード機能の追加
5. **デプロイ**: Cloud Runへのデプロイと環境変数の設定

## 注意事項

- LLM統合は環境変数`USE_LLM=true`で有効化されます
- 環境変数が設定されていない場合、自動的にモックモードにフォールバックします
- 出力ファイルは`outputs/`ディレクトリに保存されます（Gitにコミットしないよう注意）
- Gemini 3が利用できない場合は、自動的に`gemini-pro`にフォールバックします
