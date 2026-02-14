# Helm 開発プロジェクト

人とAIでできた組織を賢くする - Helmの開発リポジトリ

## 概要

Helmは、**人の責任・判断・意思決定**に焦点を当てたAIエージェントです。既存のAIエージェントがタスクや成果物を最適化するのに対し、Helmは「誰が・いつ・どう判断するか」が曖昧で、意思決定が遅れたり歪んだりする問題を検知し、改善します。

会議やチャットから「誰が・いつ・どう判断すべきか」の問題を検知し、適切な人に判断を促すシステムです。従来の「人がAIを呼び出す」から**「AIが人を呼び出す」**へ転換することで、判断の遅れや責任の曖昧さなどを自動検知し、適切なタイミングで適切な人に判断を求める仕組みを実現します。

> **「AIを賢くするのではない。"人とAIでできた組織"を賢くする。」**

## 主な機能

### ① 多角的な評価・判断システム（ハイブリッド評価）

Helmは、**ルールベースとマルチ視点LLMを組み合わせたハイブリッド評価**により、見落としのない統合判断を実現します。

**ルールベース分析**では、KPI下方修正回数、撤退議論の有無、判断集中率などの定量的指標に基づいて、安全側のベースライン評価を行います。

**マルチ視点LLM分析**では、同じ会議ログとチャットログを、4つの異なる視点から評価します：

- **経営者視点**: 全社の業績・リスク・ステークホルダー責任の観点から評価
- **経営企画視点**: KPI・事業ポートフォリオ・撤退/投資判断の観点から評価
- **現場視点**: 実行可能性と現場負荷の観点から評価
- **ガバナンス視点**: 報告遅延・隠れたリスク・コンプライアンスの観点から評価

これらの評価結果を**アンサンブルスコアリング**（0.6×ルール + 0.4×LLM）で統合することで、単一の評価軸では見落としがちな問題も、複数の視点から検知できるようになります。検知された問題は事前定義されたパターン（B1_正当化フェーズ、ES1_報告遅延、A2_撤退判断の遅れなど）に割り当てられ、アラートが作成されます。

### ② AIが人を呼び出し、判断を依頼

判断の遅れや責任の曖昧さなどを検知すると、Helmは自動で**役員 / 部長 / スタッフ**を特定し、判断・承認を依頼します。人がAIを監視するのではなく、**AIが会議やチャットの状況を監視し、必要なときに人に判断を求める**という逆転の発想を実現しています。責任モデル（RACI・組織グラフ・承認フロー）に基づいて適切なロールを決定し、「なぜこの人に判断を求めるべきか」を説明できる形で生成します。

### ③ 学習・改善PDCAの自動化

Helmは、観測（会議・チャットの取得）→ 評価（問題検知・スコアリング）→ 介入（経営層へエスカレーション）→ 実行（AI自律タスク実行）→ 結果取得（再観測で検証）のループを自動で回します。**どんなときに判断が遅れやすいか、責任が曖昧になりやすいか**を学習し、時間とともに**判断の仕組みそのものが改善されていく**仕組みを実現します。

### AI自律実行（ADKベースのマルチエージェントシステム）

経営層の承認後、Helmは**ADK (Agent Development Kit)** を使用したマルチエージェントシステムで自律的にタスクを実行します：

- **調査エージェント** (ResearchAgent): 市場データの検索・分析（将来: Vertex AI Search）
- **分析エージェント** (AnalysisAgent): 社内データの取得・財務シミュレーション（将来: Google Drive API）
- **資料エージェント**: 3案比較資料の自動生成・保存
- **通知エージェント** (NotificationAgent): メッセージ生成・送信（Phase1: ドラフトのみ、将来: Chat/Gmail API）
- **会議調整** (CalendarAgent): 会議アジェンダの更新（設計段階）

**Phase1（実装完了）**: モック実装とADK統合、フォールバック対応
**Phase2（実装予定）**: 実API統合（Vertex AI Search、Google Drive、Chat/Gmail API）

### ガバナンス・運用まわり（実装済み）

Helmは「監視ツール」ではなく、**意思決定ガバナンスの最適化**を目的とした設計です。取得範囲は特定プロジェクト・ワークスペースに限定し、同意・告知を明示。匿名化・保持期間・監査・誤検知時の責任境界を設計済みです。

- **認証**: API Key ＋ ロール（`X-API-Key` ヘッダ）。環境変数 `API_KEYS` で有効化。オーナーキー1本の例は [backend README](./backend/README.md#api-key-認証オーナーキーで有効化) を参照。
- **誤検知フィードバック・精度指標**: `POST /api/feedback/false-positive`、`GET /api/metrics/accuracy` で精度改善のためのフィードバックと指標取得。
- **監査ログ**: アクション記録と `GET /api/audit/logs` での取得。各エントリにハッシュチェーン付与、`GET /api/audit/verify` で改ざん検証可能。
- **取得範囲・サプレッション**: 取得対象のホワイトリスト（会議/チャットID）、検知のサプレッション条件（パターン＋リソース）を設定可能。
- **データ保存期間**: 原文（meetings/chats/materials）はデフォルト7日で破棄（二層保持モデル）。`POST /api/admin/retention/cleanup` による定期削除。設計は [data-retention.md](./docs/data-retention.md)。
- **冪等性**: 同一 approval_id に対する execute の二重実行を防ぐ（設計は [idempotency-execute.md](./docs/idempotency-execute.md)）。
- **定義ドキュメント駆動**: 組織グラフ・RACI・承認フローを JSON で管理（`backend/config/definitions/`）。EscalationEngine が RACI に基づきターゲットロールと承認フローを決定し、多段階承認をサポート。

将来拡張の設計（オーナーシップ、マルチテナント、ジョブキュー、通知ポリシー）は [docs/future/](./docs/future/) を参照。

### 現状の開発状況とネクストステップ

- **現状**: コア機能（データ取り込み / 検知・評価 / アラート・承認 / AI自律実行）、ガバナンス・運用（認証・監査・誤検知・サプレッション・保存期間・冪等性）、定義ドキュメント（組織グラフ・RACI・承認フロー）まで実装済み。Cloud Run / Vercel デプロイ済み。
- **ネクストステップ**:
  - **短期・中期**: ADK本実装（実API統合）、デモから汎用機能化、永続化（Firestore）、会議調整・作成
  - **長期**: マルチテナント・ジョブキュー・通知ポリシー・オーナーシップ（設計は [docs/future/](./docs/future/)）

詳細は [開発状況サマリー](./docs/status/DEVELOPMENT_STATUS_SUMMARY.md) と [次のステップ](./docs/status/NEXT_STEPS.md) を参照。

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
│   ├── config/
│   │   ├── definitions/       # 組織グラフ・RACI・承認フロー（JSON）
│   │   └── prompts/           # LLMプロンプト（ヒトが編集可能、組織グラフと同様）
│   ├── services/              # サービス層
│   │   ├── google_meet.py     # Google Meet統合
│   │   ├── google_chat.py     # Google Chat統合
│   │   ├── analyzer.py        # 構造的問題検知（ルールベース）
│   │   ├── multi_view_analyzer.py  # マルチ視点LLM分析
│   │   ├── ensemble_scoring.py     # アンサンブルスコアリング
│   │   ├── llm_service.py     # LLM統合サービス
│   │   ├── scoring.py          # スコアリングサービス
│   │   ├── escalation_engine.py    # エスカレーション判断
│   │   ├── definition_loader.py    # 定義ドキュメント読み込み
│   │   ├── responsibility_resolver.py  # RACI/承認フロー解決
│   │   ├── approval_flow_engine.py # 多段階承認フロー
│   │   ├── audit_log.py       # 監査ログ
│   │   ├── evaluation_metrics.py   # 精度指標・誤検知フィードバック
│   │   ├── retention_cleanup.py    # データ保存期間に基づく削除
│   │   ├── google_workspace.py # Google Workspace統合
│   │   ├── google_drive.py     # Google Drive統合
│   │   ├── adk_setup.py        # ADKセットアップ
│   │   └── agents/             # ADKエージェント
│   │       ├── research_agent.py      # 市場データ分析エージェント
│   │       ├── analysis_agent.py     # 社内データ統合エージェント
│   │       ├── notification_agent.py # 通知エージェント
│   │       ├── workflow_agent.py     # ワークフローエージェント
│   │       └── shared_context.py    # 共有コンテキスト
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
データ取り込み（Meet/Chat） → 検知・評価（ルールベース + 4ロールLLM） → 
アンサンブルスコアリング（0.6×ルール + 0.4×LLM） → アラート・承認 → 
AI自律実行（4エージェント並列） → 結果保存 → 再観測で検証
```

## 評価システムの仕組み（ルール×LLMによるハイブリッド評価）

### 1. ルールベース分析

定量的指標（KPI下方修正回数、撤退議論の有無、判断集中率、反対意見無視など）に基づいて、判断の遅れや責任の曖昧さに繋がる問題を検知します。これは**見逃しゼロの安全網**として機能します。

### 2. マルチ視点LLM分析

同じ会議ログとチャットログを、4つのロール視点（経営者、経営企画、現場、ガバナンス）からLLM（Gemini）で評価します。文脈理解により過剰反応を抑制しつつ、数値は正常だが「空気が異常」といったケースも検知します。

### 3. アンサンブルスコアリング

ルールベース結果とLLM結果を統合して、より保守的で信頼性の高い評価を実現します：

- **スコア計算**: `0.6 × ルールベーススコア + 0.4 × LLM平均スコア`
- **重要度・緊急度**: ルールベースと各ロールの結果のうち、**最も安全側（最も強い）**を採用
- **説明文**: ルールベースの説明と主要ロールのコメントを統合

精度指標のモニタリング（`GET /api/metrics/accuracy`）や誤検知フィードバック（`POST /api/feedback/false-positive`）により、運用しながら重みや閾値を校正していく設計です。

## 🚀 デプロイ済みサービス

### 本番環境

- **バックエンドAPI**: [https://helm-api-dsy6lzllhq-an.a.run.app](https://helm-api-dsy6lzllhq-an.a.run.app)

  - APIドキュメント: [https://helm-api-dsy6lzllhq-an.a.run.app/docs](https://helm-api-dsy6lzllhq-an.a.run.app/docs)
  - デプロイ先: Google Cloud Run (asia-northeast1)
  - LLM: 分析は Gemini 3 Flash、ADKエージェントは Gemini 2.0 Flash
- **フロントエンド**: [https://v0-helm-pdca-demo.vercel.app](https://v0-helm-pdca-demo.vercel.app)

  - デプロイ先: Vercel
  - フレームワーク: Next.js 16

### デプロイ日

- **バックエンド**: 2025年2月1日
- **フロントエンド**: 2025年1月31日

## 技術スタック

### バックエンド

- **フレームワーク**: FastAPI
- **言語**: Python 3.11
- **LLM**: Google Gemini（Gen AI SDK）。分析・タスク生成は Gemini 3 Flash、ADKエージェントは Gemini 2.0 Flash（`LLM_MODEL` / `ADK_MODEL` で変更可）
- **ADK**: Google Agent Development Kit (`google-adk`) - マルチエージェントシステム
- **Google API**: `google-api-python-client`, `google-auth-oauthlib`
- **テスト**: pytest
- **デプロイ**: Google Cloud Run

### フロントエンド

- **フレームワーク**: Next.js 16.0.10 (Turbopack)
- **言語**: TypeScript
- **UI**: React, Tailwind CSS
- **状態管理**: React Hooks

## セキュリティ

### 簡易脅威モデルと対策状況

| 脅威 | 対策状況 | 備考 |
|------|----------|------|
| 認証 bypass | **実装済み** | API Key + ロール（`X-API-Key`）。未設定時は認証無効。 |
| 権限逸脱 | **実装済み** | ロールベースアクセス制御。会議・チャットへのアクセスをロールで分離。 |
| データ漏洩 | **実装済み** | マスキング（個人名→役職、機微情報）、保持期間による自動削除、原文はデフォルト7日で破棄。 |
| DoS / 過負荷 | **実装済み** | レート制限（1分あたりNリクエスト、環境変数 `RATE_LIMIT_REQUESTS_PER_MINUTE`）。 |
| コスト暴騰（LLM） | **実装済み** | 日次トークン上限（環境変数 `LLM_DAILY_TOKEN_LIMIT`）。超えた場合はモックフォールバック。 |
| プロンプトインジェクション | **設計済み** | LLM入力は構造化データに限定、ユーザー自由入力は経由しない設計。 |
| 監査ログ改ざん | **実装済み** | 各エントリにハッシュチェーン付与。`GET /api/audit/verify` で検証可能。 |

### セキュリティ設計TODO（優先度付き）

- **高**: OIDC/IAP または Workspace 連携による認証強化（プロダクション向け）— 未実装
- **中**: 脅威モデルの詳細化と定期レビュー — 本READMEに簡易版を記載済み
- **低**: WORM 相当の監査ログ保存（クラウドストレージ連携）— 設計検討中

### 関連ドキュメント

- [認証設計（API Key）](./docs/auth-api-key-roles.md)
- [データ保存期間](./docs/data-retention.md)

---

## ドキュメント

- [📑 ドキュメント一覧](./DOCUMENTATION_INDEX.md) - 全ドキュメントのインデックス
- [📐 アーキテクチャドキュメント](./ARCHITECTURE.md) - システム全体の設計
- [📖 APIドキュメント](./backend/API_DOCUMENTATION.md) - 全APIエンドポイントの詳細
- [🔧 開発者ガイド](./docs/guides/DEVELOPER_GUIDE.md) - 開発者向けガイド
- [認証設計（API Key）](./docs/auth-api-key-roles.md) | [データ保存期間](./docs/data-retention.md) | [冪等性（execute）](./docs/idempotency-execute.md) | [将来実装（docs/future/）](./docs/future/)
- [バックエンドセットアップガイド](./backend/SETUP.md)
- [ADKセットアップガイド](./backend/ADK_SETUP.md) - ADKベースのマルチエージェントシステムのセットアップ
- [テスト実行サマリー](./backend/TEST_SETUP_SUMMARY.md) - テストの実行方法

## 提出物要件

- [x] GitHubリポジトリ（公開）
- [x] デプロイURL（動作確認可能）
  - バックエンド: https://helm-api-dsy6lzllhq-an.a.run.app
  - フロントエンド: https://v0-helm-pdca-demo.vercel.app
- [x] Zenn記事（概要、アーキテクチャ図、デモ動画）
  - https://zenn.dev/charles_389no/articles/f4adff7b7bcaf8
