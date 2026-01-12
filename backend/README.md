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
- 構造的問題検知（Vertex AI / Gemini）
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

## 開発

### 実API統合完了 ✅

Google API統合が完了しました：
- ✅ Google Drive API（ファイル保存・ダウンロード）
- ✅ Google Docs API（ドキュメント作成）
- ✅ Google Chat API（メッセージ取得）
- ✅ Google Meet API（議事録取得の準備）

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

