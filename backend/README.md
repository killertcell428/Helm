# Helm Backend API

HelmのバックエンドAPIサーバー。Googleサービス統合とAI自律実行を提供します。

## 📚 ドキュメント

- [🚀 クイックスタートガイド](../QUICKSTART.md) - 初心者向け起動手順
- [🔧 セットアップガイド](./SETUP.md) - 詳細なセットアップ手順
- [📖 APIドキュメント](./API_DOCUMENTATION.md) - 全APIエンドポイントの詳細
- [📐 アーキテクチャドキュメント](../ARCHITECTURE.md) - システム全体の設計

## 機能

- Google Meet議事録の取り込み
- Google Chatログの取り込み
- **マルチ視点評価システム**による構造的問題検知
  - ルールベース分析（定量的指標に基づく検知）
  - マルチ視点LLM分析（4つのロール視点から評価）
  - アンサンブルスコアリング（統合評価）
- Executive呼び出しと承認
- Googleサービス経由でのタスク実行
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

**注意:** 現在はモックデータを使用しているため、`requirements_minimal.txt` で十分です。Windows環境でインストールエラーが発生する場合も、`requirements_minimal.txt` を使用してください。

## APIエンドポイント

- `POST /api/meetings/ingest` - 議事録取り込み
- `POST /api/chat/ingest` - チャット取り込み
- `POST /api/analyze` - 構造的問題検知
- `GET /api/analysis/{id}` - 分析結果取得
- `POST /api/escalate` - Executive呼び出し
- `POST /api/approve` - Executive承認
- `POST /api/execute` - AI自律実行開始
- `GET /api/execution/{id}` - 実行状態取得
- `GET /api/execution/{id}/results` - 実行結果取得

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
- ✅ LLM統合（Gemini / Gen AI SDK）

**詳細**: [REAL_DATA_IMPLEMENTATION.md](./REAL_DATA_IMPLEMENTATION.md) を参照してください。

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

