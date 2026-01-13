# Helm 開発プロジェクト

組織を賢くするAI - Helmの開発リポジトリ

## 📚 ドキュメント

**初めての方はこちらから:**
- [🚀 クイックスタートガイド](./docs/guides/QUICKSTART.md) - 初心者向け起動手順
- [📐 アーキテクチャドキュメント](./ARCHITECTURE.md) - システム全体の設計
- [📑 ドキュメント一覧](./DOCUMENTATION_INDEX.md) - 全ドキュメントのインデックス

## プロジェクト構成

```
Dev/
├── app/
│   └── v0-helm-demo/          # フロントエンド（Next.js）
│       ├── app/
│       │   └── demo/
│       │       └── case1/      # Case1デモページ
│       └── lib/
│           └── api.ts         # APIクライアント
├── backend/                    # バックエンド（Python FastAPI）
│   ├── main.py                # メインAPI
│   ├── services/              # サービス層
│   │   ├── google_meet.py
│   │   ├── google_chat.py
│   │   ├── analyzer.py
│   │   ├── google_workspace.py
│   │   └── google_drive.py
│   ├── schemas/               # データスキーマ
│   │   └── firestore.py
│   └── requirements.txt
└── Architectures/             # アーキテクチャ設計資料
```

## クイックスタート

### バックエンドの起動

```bash
cd Dev/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### フロントエンドの起動

```bash
cd Dev/app/v0-helm-demo
pnpm install
pnpm dev
```

フロントエンドは `http://localhost:3000` で起動します。

## 実装フロー

```
Google Meet → 議事録・チャット取得 → 重要性・緊急性評価 → 
人が承認/指示 → Googleサービス経由でリサーチ・分析・資料作成 → 
結果をアプリに返してダウンロード → 次回会議へ
```

## 現在の実装状況

### Week 2完了 ✅

**実装完了項目**:
- ✅ Google API統合（Drive, Docs, Chat, Meet）
- ✅ 実データ実装（フロントエンド・バックエンド）
- ✅ エラーハンドリングの改善
- ✅ 全機能の動作確認

**詳細**: [docs/status/WEEK2_SUMMARY.md](./docs/status/WEEK2_SUMMARY.md) を参照してください。

### 実装済み

- ✅ バックエンドAPI基盤
- ✅ Googleサービス統合（実API + モックフォールバック）
- ✅ 構造的問題検知（ルールベース）
- ✅ フロントエンド連携
- ✅ 実データ表示機能
- ✅ エラーハンドリング（ユーザーフレンドリーなメッセージ）

### 実装予定 / 進行中

- ⏳ Vertex AI / Gemini統合（準備完了、実API統合待ち）
- ⏳ テストの拡充（E2E + パフォーマンス）
- ⏳ パフォーマンス最適化

## ドキュメント

- [📑 ドキュメント一覧](./DOCUMENTATION_INDEX.md) - 全ドキュメントのインデックス
- [📊 プロジェクト状況](./docs/status/PROJECT_STATUS.md) - 現在の実装状況
- [📝 Week 2サマリー](./docs/status/WEEK2_SUMMARY.md) - Week 2の実装サマリー
- [🚀 次のステップ](./docs/status/NEXT_STEPS.md) - 次のステップ候補
- [バックエンドセットアップガイド](./backend/SETUP.md)
- [テスト実行サマリー](./backend/TEST_SETUP_SUMMARY.md) - テスト（ユニット/統合/E2E/パフォーマンス）の実行方法
- [アーキテクチャ設計](./Architectures/)

## 開発スケジュール

- **Week 1（1/20-1/26）**: 基盤構築とGoogle API統合 ✅
- **Week 2（1/27-2/2）**: コア機能実装・実API統合・実データ実装 ✅
- **Week 3（2/3-2/9）**: 機能強化・品質向上
- **Week 4（2/10-2/15）**: 提出物準備

**次のステップ**: [docs/status/NEXT_STEPS.md](./docs/status/NEXT_STEPS.md) を参照してください。

## 提出物要件

- [ ] GitHubリポジトリ（公開）
- [ ] デプロイURL（動作確認可能）
- [ ] Zenn記事（概要、アーキテクチャ図、デモ動画3分）

