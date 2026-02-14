# デプロイ前チェックリスト

最終確認日: 2025年2月

## テスト結果サマリー

| カテゴリ | 結果 | 備考 |
|----------|------|------|
| **ユニットテスト** | ✅ 23件 成功 | analyzer, escalation, scoring |
| **フロントエンドビルド** | ✅ 成功 | Next.js 16.0.10 |
| **統合テスト** | ⚠ 要サーバー起動 | `uvicorn main:app --reload --port 8000` 起動後に実行 |
| **E2Eテスト** | ⚠ 要サーバー起動 | 多段階承認対応済み |

## デプロイ前の確認手順

### 1. バックエンド

```bash
cd Dev/backend
python -m pytest tests/unit -v -q
uvicorn main:app --host 0.0.0.0 --port 8000  # ローカル起動確認
```

### 2. フロントエンド

```bash
cd Dev/app/v0-helm-demo
pnpm run build
pnpm dev  # ローカル起動確認
```

### 3. 環境変数（本番デプロイ時）

- `GOOGLE_API_KEY` または `GEMINI_API_KEY`: Gemini API
- `LLM_MODEL`: 分析・タスク生成・ADKエージェント共通（例: gemini-3-flash-preview）
- `USE_LLM=true`: LLM有効化
- `API_KEYS`: API認証（オーナーキー等）
- Cloud Run / Vercel 用のデプロイ設定

### 4. プロンプト・設定ファイル

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
