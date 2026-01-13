# Helm 開発プロジェクト

組織を賢くするAI - Helmの開発リポジトリ

## 概要

Helmは、組織の意思決定プロセスを監視し、構造的問題を検知して改善を提案するAIシステムです。Google Meetの議事録やGoogle Chatのログを分析し、意思決定の遅延や構造的な問題を自動的に検出します。

## 主な機能

### 構造的問題検知

Helmは、会議議事録とチャットログから以下のような構造的問題を検知します：

- **B1_正当化フェーズ**: KPI悪化が続いているにも関わらず、戦略変更の議論が行われない
- **ES1_報告遅延**: リスク認識があるにも関わらず、上位への報告が遅延している
- **A2_撤退判断の遅れ**: 事業の悪化が明らかなのに、撤退やピボットの議論が行われない

### マルチ視点評価システム

Helmは、複数の視点から同一のデータを評価することで、より精度の高い判断を実現します：

- **経営者視点（Executive）**: 全社の業績・リスク・ステークホルダー責任の観点から評価
- **経営企画視点（Corp Planning）**: KPI・事業ポートフォリオ・撤退/投資判断の観点から評価
- **現場視点（Staff）**: 実行可能性と現場負荷の観点から評価
- **ガバナンス視点（Governance）**: 報告遅延・隠れたリスク・コンプライアンスの観点から評価

各視点の評価結果をアンサンブル（統合）することで、人間の経営判断に近い精度で構造リスクを評価します。

### AI自律実行

Executiveの承認後、Helmは自律的に以下のタスクを実行します：

- 市場データ分析
- 社内データ統合
- 3案比較資料の自動生成
- 関係部署への事前通知
- 会議アジェンダの更新

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
│       │       ├── case1/      # Case1デモページ
│       │       ├── case2/      # Case2デモページ
│       │       └── case3/      # Case3デモページ
│       └── lib/
│           └── api.ts         # APIクライアント
├── backend/                    # バックエンド（Python FastAPI）
│   ├── main.py                # メインAPI
│   ├── services/              # サービス層
│   │   ├── google_meet.py     # Google Meet統合
│   │   ├── google_chat.py     # Google Chat統合
│   │   ├── analyzer.py        # 構造的問題検知（ルールベース）
│   │   ├── multi_view_analyzer.py  # マルチ視点LLM分析
│   │   ├── ensemble_scoring.py     # アンサンブルスコアリング
│   │   ├── llm_service.py     # LLM統合サービス
│   │   ├── scoring.py          # スコアリングサービス
│   │   ├── google_workspace.py # Google Workspace統合
│   │   └── google_drive.py     # Google Drive統合
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

## システムフロー

```
Google Meet → 議事録・チャット取得 → マルチ視点評価（ルールベース + LLM） → 
アンサンブルスコアリング → Executive承認 → AI自律実行 → 
結果をアプリに返してダウンロード → 次回会議へ
```

## 評価システムの仕組み

### 1. ルールベース分析

定量的な指標（KPI下方修正回数、撤退議論の有無、判断集中率など）に基づいて構造的問題を検知します。これは安全側のベースラインとして機能します。

### 2. マルチ視点LLM分析

同じ会議ログとチャットログを、4つの異なる視点（経営者、経営企画、現場、ガバナンス）からLLM（Gemini）で評価します。各視点は独自のプロンプトを使用し、それぞれの立場から構造的リスクを評価します。

### 3. アンサンブルスコアリング

ルールベース分析結果とマルチ視点LLM分析結果を統合して、最終的なスコアと重要度・緊急度を決定します：

- **スコア計算**: `最終スコア = 0.6 × ルールベーススコア + 0.4 × LLM平均スコア`
- **重要度・緊急度**: ルールベースと各ロールの結果のうち、最も強い（安全側）を採用

このアプローチにより、単一の評価軸では見落としがちな問題も、複数の視点から検知できるようになります。

## 技術スタック

### バックエンド
- **フレームワーク**: FastAPI
- **言語**: Python 3.12
- **LLM**: Google Gemini 2.0 Flash (Gen AI SDK)
- **Google API**: `google-api-python-client`, `google-auth-oauthlib`
- **テスト**: pytest

### フロントエンド
- **フレームワーク**: Next.js 16.0.10 (Turbopack)
- **言語**: TypeScript
- **UI**: React, Tailwind CSS
- **状態管理**: React Hooks

## ドキュメント

- [📑 ドキュメント一覧](./DOCUMENTATION_INDEX.md) - 全ドキュメントのインデックス
- [📐 アーキテクチャドキュメント](./ARCHITECTURE.md) - システム全体の設計
- [📖 APIドキュメント](./backend/API_DOCUMENTATION.md) - 全APIエンドポイントの詳細
- [🔧 開発者ガイド](./docs/guides/DEVELOPER_GUIDE.md) - 開発者向けガイド
- [バックエンドセットアップガイド](./backend/SETUP.md)
- [テスト実行サマリー](./backend/TEST_SETUP_SUMMARY.md) - テストの実行方法

## 提出物要件

- [ ] GitHubリポジトリ（公開）
- [ ] デプロイURL（動作確認可能）
- [ ] Zenn記事（概要、アーキテクチャ図、デモ動画3分）
