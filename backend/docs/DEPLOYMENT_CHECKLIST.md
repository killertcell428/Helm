# デプロイ前チェックリスト

最終確認日: 2026年2月

## テスト結果サマリー

| カテゴリ | 結果 | 備考 |
|----------|------|------|
| **ユニットテスト** | ✅ 成功 | analyzer, escalation, scoring |
| **フロントエンドビルド** | ✅ 成功 | Next.js 16.0.10 |
| **統合テスト** | ✅ 要サーバー起動 | `uvicorn main:app --reload --port 8000` 起動後に実行 |
| **Case1デモフロー** | ✅ 成功 | `tests/integration/test_case1_demo_flow.py` |

## デプロイ前の確認手順

### 1. バックエンド

```bash
cd Dev/backend
pip install -r requirements_test.txt  # pytest 等（初回のみ）
python -m pytest tests/unit -v -q
uvicorn main:app --host 0.0.0.0 --port 8000  # ローカル起動確認（別ターミナルで）
python -m pytest tests/integration/test_case1_demo_flow.py -v  # Case1フロー検証（約1分）
```

### 2. フロントエンド

```bash
cd Dev/app/v0-helm-demo
pnpm run build
pnpm dev  # ローカル起動確認
```

### 3. デプロイ検証スクリプト（推奨）

バックエンド・フロントエンド両方起動後に実行:

```bash
# 初回のみ: テスト用依存関係をインストール
cd Dev/backend && pip install -r requirements_test.txt

# 検証実行（プロジェクトルートから）
python Dev/scripts/verify_case1_deploy.py
```

- バックエンド/フロントエンドのヘルスチェック
- Case1ページの存在確認
- Case1 API統合テスト（約1分）

### 4. Case1デモのブラウザ検証（E2E）

1. バックエンド起動: `cd Dev/backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000`
2. フロントエンド起動: `cd Dev/app/v0-helm-demo && pnpm dev`
3. ブラウザで http://localhost:3000/demo/case1 を開く
4. 以下を手動で確認:
   - パターンA/B/Cのいずれかを選択 → 「次へ」
   - 「データ受領」→「次へ」→「分析完了」→「次へ」
   - 「承認待ち」で「承認する」を選択 → 「次へ」
   - 「実行中」で進捗が0→100%に進み、約15〜20秒で「結果」画面に遷移すること
   - 「実行結果」が表示され、「次へ」で「次のサイクル」に遷移すること

### 5. 環境変数（本番デプロイ時）

- `GOOGLE_API_KEY` または `GEMINI_API_KEY`: Gemini API
- `LLM_MODEL`: 分析・タスク生成・ADKエージェント共通（例: gemini-3-flash-preview）
- `USE_LLM=true`: LLM有効化
- `API_KEYS`: API認証（オーナーキー等）
- Cloud Run / Vercel 用のデプロイ設定

### 6. プロンプト・設定ファイル

- `config/definitions/`: 組織グラフ、RACI、承認フロー
- `config/prompts/`: LLMプロンプト（編集可能、フォールバックあり）

## 既知の注意点

- **google.generativeai**: FutureWarning（将来 google.genai へ移行推奨）
- **Pydantic @validator**: 非推奨警告（@field_validator へ移行推奨）
- **baseline-browser-mapping**: npm パッケージのアップデート推奨

## 変更履歴（今回の改修）

1. プロンプト外部ファイル化（config/prompts/）
2. ADKモデルをLLM評価と同じに統一（ADK_MODEL / LLM_MODEL）
3. E2E・統合テストの多段階承認対応
4. **Case1「実行中」無限ループ修正** (2026-02):
   - `handleActionDecided` の戻り値を `handleAiExecuting` に渡す（setState非同期のため approvalId が null だった）
   - モック進捗を並行実行（15秒で100%、バックエンド応答なしでも次へ進む）
   - タイムアウトを20秒に短縮
   - API失敗時のモック結果フォールバック
