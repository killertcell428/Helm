# Helm Backend API

HelmのバックエンドAPIサーバー。Googleサービス統合とAI自律実行を提供します。

## 🚀 デプロイ済みサービス

**本番環境**: [https://helm-api-dsy6lzllhq-an.a.run.app](https://helm-api-dsy6lzllhq-an.a.run.app)

- **APIドキュメント**: [https://helm-api-dsy6lzllhq-an.a.run.app/docs](https://helm-api-dsy6lzllhq-an.a.run.app/docs)
- **デプロイ先**: Google Cloud Run (asia-northeast1)
- **LLM**: Gemini 3 Flash Preview
- **デプロイ日**: 2025年2月1日

詳細は [デプロイ関連ドキュメント](../docs/gcloud/) を参照してください。

## 📚 ドキュメント

- [🚀 クイックスタートガイド](../QUICKSTART.md) - 初心者向け起動手順
- [🔧 セットアップガイド](./SETUP.md) - 詳細なセットアップ手順
- [📖 APIドキュメント](./API_DOCUMENTATION.md) - 全APIエンドポイントの詳細
- [📐 アーキテクチャドキュメント](../ARCHITECTURE.md) - システム全体の設計
- [🤖 ADKセットアップガイド](./ADK_SETUP.md) - ADKベースのマルチエージェントシステムのセットアップ

## 機能

- Google Meet議事録の取り込み
- Google Chatログの取り込み
- **マルチ視点評価システム**による構造的問題検知
  - ルールベース分析（定量的指標に基づく検知）
  - マルチ視点LLM分析（4つのロール視点から評価）
  - アンサンブルスコアリング（統合評価）
- Executive呼び出しと承認
- **ADKベースのマルチエージェントシステム**によるAI自律実行
  - ResearchAgent（市場データ分析）
  - AnalysisAgent（社内データ統合）
  - NotificationAgent（通知生成）
  - DocumentAgent（資料生成 - Google Docs API）
- 結果のダウンロード

## セットアップ

```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール（最小限版・推奨）
pip install -r requirements_minimal.txt

# または、すべての依存関係をインストール
# pip install -r requirements.txt

# 環境変数の設定（オプション・現在は不要）
# cp .env.example .env
# .envファイルを編集して必要な設定を追加

# サーバーの起動
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Key 認証（オーナーキーで有効化）

認証を有効にすると、`/api/*` へのリクエストに **`X-API-Key` ヘッダ必須**になります。

1. **オーナー用キーを1本だけ使う場合**  
   `.env` に以下を追加（UTF-8 で保存）。  
   `API_KEYS=[{"key":"helm-owner-dev-key","role":"owner"}]`  
   本番ではキーを必ず別の値に変更してください。
2. サーバー再起動後、キーなしで `/api/metrics/accuracy` などにアクセス → **401**。  
   ヘッダ `X-API-Key: helm-owner-dev-key` を付ける → **200**。

サンプルは `backend/.env.example` を参照。詳細は [認証設計](../docs/auth-api-key-roles.md) を参照。

**注意:** 現在はモックデータを使用しているため、`requirements_minimal.txt` で十分です。Windows環境でインストールエラーが発生する場合も、`requirements_minimal.txt` を使用してください。

## APIエンドポイント

- `POST /api/meetings/ingest` - 議事録取り込み
- `POST /api/chat/ingest` - チャット取り込み
- `POST /api/analyze` - 構造的問題検知
- `GET /api/analysis/{id}` - 分析結果取得
- `POST /api/escalate` - Executive呼び出し
- `POST /api/approve` - Executive承認（多段階承認フロー対応・`reject`・`approver_role_id`）
- `POST /api/execute` - AI自律実行開始（冪等: 同一 approval_id は既存実行を返す）
- `GET /api/execution/{id}` - 実行状態取得
- `GET /api/execution/{id}/results` - 実行結果取得
- `POST /api/feedback/false-positive` - 誤検知フィードバック
- `GET /api/metrics/accuracy` - 精度指標取得
- `GET /api/audit/logs` - 監査ログ取得
- `POST /api/admin/retention/cleanup` - データ保存期間に基づく削除

## 評価システム

Helmは、**マルチ視点評価システム**を採用しています。このシステムは、ルールベース分析とマルチ視点LLM分析をアンサンブルして、より精度の高い評価を実現します。

### 評価の流れ

1. **ルールベース分析** (`StructureAnalyzer`)
   - 定量的指標（KPI下方修正回数、撤退議論の有無、判断集中率など）に基づいて構造的問題を検知
   - 安全側のベースラインとして機能

2. **マルチ視点LLM分析** (`MultiRoleLLMAnalyzer`)
   - 同じデータを4つの異なる視点からLLM（Gemini）で評価
   - Executive視点（重み: 0.4）、Corp Planning視点（重み: 0.3）、Staff視点（重み: 0.2）、Governance視点（重み: 0.1）

3. **アンサンブルスコアリング** (`EnsembleScoringService`)
   - ルールベース結果とLLM結果を統合
   - スコア計算: `0.6 × ルールベース + 0.4 × LLM平均`
   - 重要度・緊急度: 安全側（最も強い）を採用

詳細は [アーキテクチャドキュメント](../ARCHITECTURE.md) を参照してください。

## 開発

### 実API統合完了 ✅

Google API統合が完了しました：
- ✅ Google Drive API（ファイル保存・ダウンロード）
- ✅ Google Docs API（ドキュメント作成）
- ✅ Google Chat API（メッセージ取得）
- ✅ Google Meet API（議事録取得）
- ✅ LLM統合（Gemini 3 Flash Preview / Gen AI SDK）

### 本番デプロイ完了 ✅

- ✅ Google Cloud Runへのデプロイ完了
- ✅ Gemini 3 Flash Previewが正常に動作
- ✅ マルチ視点LLM分析が正常に完了
- ✅ 環境変数設定完了（GOOGLE_API_KEY, USE_LLM, GOOGLE_CLOUD_PROJECT_ID）

**詳細**: [REAL_DATA_IMPLEMENTATION.md](./REAL_DATA_IMPLEMENTATION.md) を参照してください。

### ADKベースのマルチエージェントシステム実装完了 ✅

**Phase1（実装完了）**:
- ✅ ADK (Agent Development Kit) のセットアップ
- ✅ ResearchAgent、AnalysisAgent、NotificationAgentの実装
- ✅ モック実装とフォールバック対応
- ✅ SharedContextによるエージェント間のデータ共有
- ✅ テストスクリプトによる動作確認完了

**Phase2（実装予定）**:
- Vertex AI Search API統合（市場データ検索）
- Google Drive API統合（社内データ取得）
- Google Chat/Gmail API統合（通知送信）

**詳細**: [ADK_SETUP.md](./ADK_SETUP.md) を参照してください。

### 認証方式

- **OAuth認証**: 個人のGoogleアカウントで使用可能（推奨）
  - セットアップ: [QUICK_SETUP_PERSONAL_DRIVE.md](./QUICK_SETUP_PERSONAL_DRIVE.md)
- **サービスアカウント**: Google Workspace環境（共有ドライブ必要）
  - セットアップ: [SETUP_SHARED_DRIVE.md](./SETUP_SHARED_DRIVE.md)
- **モックモード**: 認証情報が設定されていない場合、自動的にモックモードにフォールバック

### テスト

- **ユニットテスト**: `pytest tests/unit/`
- **統合テスト**: `pytest tests/integration/`
- **E2Eテスト**: `pytest tests/e2e/`
- **Swagger UI**: http://localhost:8000/docs で各エンドポイントをテスト

