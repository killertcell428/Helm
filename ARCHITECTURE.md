# Helm アーキテクチャドキュメント

## 概要

Helmは、組織の意思決定プロセスを監視し、構造的問題を検知して改善を提案するAIシステムです。

## システム全体図

```
┌─────────────────────────────────────────────────────────────┐
│                        フロントエンド                         │
│                    (Next.js + TypeScript)                    │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Case1      │  │   Case2      │  │   Case3      │      │
│  │   デモページ   │  │   デモページ   │  │   デモページ   │      │
│  └──────┬───────┘  └──────────────┘  └──────────────┘      │
│         │                                                      │
│  ┌──────▼───────┐                                            │
│  │  API Client  │  (lib/api.ts)                              │
│  └──────┬───────┘                                            │
└─────────┼─────────────────────────────────────────────────────┘
          │ HTTP REST API
          │
┌─────────▼─────────────────────────────────────────────────────┐
│                      バックエンドAPI                            │
│                    (Python FastAPI)                            │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              APIエンドポイント層                        │   │
│  │  /api/meetings/ingest, /api/analyze, etc.            │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐   │
│  │              サービス層                                │   │
│  │                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │ Google Meet  │  │ Google Chat  │                │   │
│  │  │   Service    │  │   Service    │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  │                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │  Structure   │  │  LLM Service │                │   │
│  │  │   Analyzer   │  │  (Gemini)     │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  │                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │  Multi-Role  │  │  Ensemble     │                │   │
│  │  │  LLM Analyzer│  │  Scoring      │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  │                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │  Scoring     │  │  Escalation   │                │   │
│  │  │   Service    │  │   Engine      │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  │                                                       │   │
│  │  ┌──────────────┐                                    │   │
│  │  │  Output      │                                    │   │
│  │  │   Service     │                                    │   │
│  │  └──────────────┘                                    │   │
│  │                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │  Workspace   │  │  Google      │                │   │
│  │  │   Service    │  │  Drive       │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  │                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │  ADK Setup   │  │  ADK Agents  │                │   │
│  │  │   Service    │  │  (Research,  │                │   │
│  │  │              │  │   Analysis,   │                │   │
│  │  │              │  │   Notification)│              │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  └───────────────────────────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐   │
│  │              データ層（将来: Firestore）                │   │
│  │            （現在: インメモリストレージ）                 │   │
│  └───────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

## データフロー

### 1. データ取り込みフロー

```
Google Meet/Chat
      │
      ▼
[議事録/チャット取得]
      │
      ▼
[パース処理]
      │
      ├─→ [発言者抽出]
      ├─→ [KPI検出]
      ├─→ [撤退議論検出]
      └─→ [リスク検出]
      │
      ▼
[構造化データ]
      │
      ▼
[Firestore保存] (将来)
```

### 2. 構造的問題検知フロー（マルチ視点評価システム）

```
[構造化データ]
      │
      ├─────────────────────────────────────┐
      │                                     │
      ▼                                     ▼
[ルールベース分析]              [マルチ視点LLM分析]
[StructureAnalyzer]              [MultiRoleLLMAnalyzer]
      │                                     │
      │                                     ├─→ [Executive視点] (重み: 0.4)
      │                                     ├─→ [Corp Planning視点] (重み: 0.3)
      │                                     ├─→ [Staff視点] (重み: 0.2)
      │                                     └─→ [Governance視点] (重み: 0.1)
      │                                     │
      │                                     ▼
      │                              [各ロールの評価結果]
      │                              (overall_score, severity, urgency, explanation)
      │
      └─────────────────────────────────────┘
                      │
                      ▼
            [アンサンブルスコアリング]
            [EnsembleScoringService]
                      │
                      ├─→ スコア計算: 0.6 × ルールベース + 0.4 × LLM平均
                      ├─→ 重要度・緊急度: 安全側（最も強い）を採用
                      └─→ 説明文: ルールベース + 主要ロールのコメント
                      │
                      ▼
            [パターン検出結果]
                      │
                      ├─→ B1_正当化フェーズ
                      ├─→ ES1_報告遅延
                      └─→ A2_撤退判断の遅れ
                      │
                      ▼
            [アラート生成 & 結果保存]
                      │
                      ├─→ [Output Service] (JSONファイル保存)
                      └─→ [レスポンス返却]
                            (findings, score, severity, urgency, 
                             multi_view, ensemble)
```

### 3. Executive呼び出しフロー

```
[アラート生成]
      │
      ▼
[エスカレーション判断]
      │
      ├─→ [責任モデル参照]
      ├─→ [組織グラフ参照]
      └─→ [ロール選択]
      │
      ▼
[Executive呼び出し]
      │
      ▼
[承認待ち]
      │
      ├─→ [承認] ──→ [AI実行開始]
      └─→ [却下] ──→ [終了]
```

### 4. AI自律実行フロー（ADKベースのマルチエージェントシステム）

```
[承認完了]
      │
      ▼
[実行計画生成] (LLM Service)
      │
      ├─→ [タスク1: 市場データ分析] ──→ [ResearchAgent (ADK)]
      ├─→ [タスク2: 社内データ統合] ──→ [AnalysisAgent (ADK)]
      ├─→ [タスク3: 資料生成] ──→ [DocumentAgent (Google Docs API)]
      ├─→ [タスク4: 通知送信] ──→ [NotificationAgent (ADK)]
      └─→ [タスク5: 会議設定] ──→ [CalendarAgent (将来実装)]
      │
      ▼
[SharedContext] (エージェント間のデータ共有)
      │
      ├─→ [ResearchAgent]
      │   ├─→ search_market_data (モック / Phase2: Vertex AI Search)
      │   └─→ analyze_market_data (モック / Phase2: Gemini)
      │
      ├─→ [AnalysisAgent]
      │   ├─→ fetch_internal_data (モック / Phase2: Google Drive API)
      │   └─→ perform_financial_simulation (モック / Phase2: Gemini)
      │
      ├─→ [NotificationAgent]
      │   ├─→ generate_notification_message (モック / Phase2: Gemini)
      │   └─→ send_notification (Phase1: ドラフトのみ / Phase2: Google Chat/Gmail API)
      │
      └─→ [DocumentAgent]
          └─→ generate_document (Google Docs API - 実装済み)
      │
      ▼
[結果保存 & ダウンロードURL生成]
      │
      ▼
[フロントエンドに結果返却] (WebSocket経由でリアルタイム更新)
```

**Phase1（実装完了）**:
- ADKベースのマルチエージェントシステム実装
- ResearchAgent、AnalysisAgent、NotificationAgentの実装
- モック実装とフォールバック対応
- SharedContextによるエージェント間のデータ共有

**Phase2（実装予定）**:
- Vertex AI Search API統合（市場データ検索）
- Google Drive API統合（社内データ取得）
- Google Chat/Gmail API統合（通知送信）

## コンポーネント詳細

### フロントエンド

#### ディレクトリ構造

```
app/v0-helm-demo/
├── app/
│   ├── demo/
│   │   ├── case1/          # Case1デモページ
│   │   ├── case2/          # Case2デモページ
│   │   └── case3/          # Case3デモページ
│   ├── layout.tsx          # レイアウト
│   └── page.tsx            # ホームページ
├── lib/
│   └── api.ts              # APIクライアント
└── components/
    └── ui/                 # UIコンポーネント
```

#### 主要コンポーネント

- **Case1Demo** (`app/demo/case1/page.tsx`)
  - 経営会議後の構造変化検知デモ
  - 8つのステートでフローを管理
  - API連携で実際のデータを表示

- **API Client** (`lib/api.ts`)
  - 全APIエンドポイントの型定義
  - エラーハンドリング
  - リクエスト/レスポンスの型安全性

### バックエンド

#### ディレクトリ構造

```
backend/
├── main.py                 # メインAPI
├── config.py               # アプリケーション設定
├── config/definitions/     # 組織グラフ・RACI・承認フロー（JSON）
│   ├── org_graph.json
│   ├── raci.json
│   └── approval_flows.json
├── services/               # サービス層
│   ├── google_meet.py      # Google Meet統合
│   ├── google_chat.py      # Google Chat統合
│   ├── analyzer.py         # 構造的問題検知（ルールベース）
│   ├── multi_view_analyzer.py  # マルチ視点LLM分析
│   ├── ensemble_scoring.py     # アンサンブルスコアリング
│   ├── llm_service.py      # LLM統合サービス（Gemini / Gen AI SDK）
│   ├── scoring.py          # スコアリングサービス
│   ├── escalation_engine.py # エスカレーション判断エンジン
│   ├── definition_loader.py # 定義ドキュメント読み込み（org_graph, raci, approval_flows）
│   ├── responsibility_resolver.py # RACI/承認フロー解決（target_roles, approval_flow_id）
│   ├── approval_flow_engine.py # 多段階承認フロー（ステージ遷移・全員承認判定）
│   ├── audit_log.py # 監査ログ
│   ├── evaluation_metrics.py # 精度指標・誤検知フィードバック
│   ├── retention_cleanup.py # データ保存期間に基づく削除
│   ├── google_workspace.py # Google Workspace統合
│   ├── google_drive.py     # Google Drive統合
│   ├── output_service.py   # 出力サービス
│   ├── adk_setup.py        # ADKセットアップ（モデル、Runner管理）
│   ├── agents/             # ADKエージェント
│   │   ├── research_agent.py      # 市場データ分析エージェント
│   │   ├── analysis_agent.py     # 社内データ統合エージェント
│   │   ├── notification_agent.py # 通知エージェント
│   │   ├── workflow_agent.py     # ワークフローエージェント
│   │   └── shared_context.py     # 共有コンテキスト
│   ├── prompts/            # LLMプロンプト
│   │   ├── analysis_prompt.py
│   │   └── task_generation_prompt.py
│   └── evaluation/         # 評価パーサー
│       └── parser.py
├── utils/                  # ユーティリティ
│   ├── logger.py           # ログ機能
│   ├── exceptions.py       # カスタム例外
│   └── error_notifier.py   # エラー通知
├── schemas/                # データスキーマ
│   └── firestore.py       # Firestoreスキーマ定義
└── requirements.txt        # 依存関係
```

#### 主要サービス

**GoogleMeetService**
- 議事録の取得とパース
- 発言者抽出、KPI検出、撤退議論検出

**GoogleChatService**
- チャットメッセージの取得とパース
- リスク検出、エスカレーション検出、反対意見検出

**LLMService**
- Gemini統合（Gen AI SDK経由）
- 構造的問題検知（LLM分析）
- タスク生成（LLM生成）
- ロール別プロンプト生成
- モックフォールバック

**MultiRoleLLMAnalyzer**
- マルチ視点LLM分析
- 4つのロール（Executive, Corp Planning, Staff, Governance）で同一データを評価
- 各ロールの重み付け（デフォルト: 0.4, 0.3, 0.2, 0.1）

**EnsembleScoringService**
- ルールベース分析結果とマルチ視点LLM分析結果の統合
- アンサンブルスコア計算（0.6 × ルールベース + 0.4 × LLM平均）
- 重要度・緊急度の安全側決定

**StructureAnalyzer**
- ルールベース分析（安全側のベースライン）
- パターン検出とスコアリング
- 定量指標の抽出（KPI下方修正回数、撤退議論の有無、判断集中率など）

**ADKエージェント（Phase1実装完了）**
- **ResearchAgent**: 市場データを収集・分析するエージェント（モック実装、Phase2でVertex AI Search統合予定）
- **AnalysisAgent**: 社内データを統合し、財務シミュレーションを実行するエージェント（モック実装、Phase2でGoogle Drive API統合予定）
- **NotificationAgent**: 関係部署への通知メッセージを生成するエージェント（Phase1ではドラフト生成のみ、Phase2でGoogle Chat/Gmail API統合予定）
- **TaskWorkflowAgent**: タスクの依存関係を管理し、エージェントを実行するワークフローエージェント
- **SharedContext**: エージェント間でデータを共有するコンテキスト管理

**ScoringService**
- スコアリングロジック
- 定量評価基準の抽出
- 重要度・緊急度の計算

**EscalationEngine**
- エスカレーション判断
- 責任モデルに基づくロール選択
- エスカレーション理由生成

**GoogleWorkspaceService**
- 市場データリサーチ
- データ分析
- 資料生成
- 通知送信

**GoogleDriveService**
- ファイル保存
- ダウンロードURL生成
- ファイル共有

**OutputService**
- 分析結果のJSONファイル保存
- タスク生成結果のJSONファイル保存
- 出力ファイルの管理

## API設計

### エンドポイント一覧

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/` | ヘルスチェック |
| POST | `/api/meetings/ingest` | 議事録取り込み |
| POST | `/api/chat/ingest` | チャット取り込み |
| POST | `/api/materials/ingest` | 資料取り込み |
| POST | `/api/analyze` | 構造的問題検知 |
| GET | `/api/analysis/{id}` | 分析結果取得 |
| POST | `/api/escalate` | Executive呼び出し |
| POST | `/api/approve` | Executive承認 |
| POST | `/api/execute` | AI自律実行開始 |
| GET | `/api/execution/{id}` | 実行状態取得 |
| GET | `/api/execution/{id}/results` | 実行結果取得 |
| WebSocket | `/api/execution/{id}/ws` | 実行進捗のリアルタイム更新 |
| GET | `/api/download/{file_id}` | ファイルダウンロードURL取得 |
| GET | `/api/outputs` | 出力ファイル一覧取得 |
| GET | `/api/outputs/{file_id}` | 出力ファイル取得 |
| POST | `/api/feedback/false-positive` | 誤検知フィードバック登録 |
| GET | `/api/metrics/accuracy` | 精度指標取得（Precision/Recall/F1、pattern_id で絞り込み可） |
| GET | `/api/audit/logs` | 監査ログ取得（user_id, action, 期間等でフィルタ） |
| POST | `/api/admin/retention/cleanup` | データ保存期間に基づく削除（日次バッチ用） |

### データモデル

#### MeetingIngestRequest
```typescript
{
  meeting_id: string;
  transcript?: string;  // オプション（空の場合はAPIから取得）
  metadata: {
    meeting_name: string;
    date: string;
    participants: string[];
  };
}
```

#### AnalysisResult
```typescript
{
  analysis_id: string;
  meeting_id: string;
  chat_id?: string;
  findings: Array<{
    pattern_id: string;
    severity: "HIGH" | "MEDIUM" | "LOW";
    description: string;
    evidence: string[];
    score: number;
    urgency?: string;
    evaluation?: {
      overall_score: number;
      importance_score: number;
      urgency_score: number;
      severity: string;
      urgency: string;
      reasons: string[];
    };
  }>;
  score: number;  // アンサンブル後の最終スコア
  severity: string;
  urgency: string;
  explanation: string;
  created_at: string;
  // LLMメタ情報
  is_llm_generated: boolean;
  llm_status: string;
  llm_model?: string;
  // マルチ視点評価結果
  multi_view?: Array<{
    role_id: string;
    weight: number;
    overall_score: number;
    severity: string;
    urgency: string;
    explanation?: string;
  }>;
  // アンサンブル結果
  ensemble?: {
    overall_score: number;
    severity: string;
    urgency: string;
    reasons?: string[];
    contributing_roles?: Array<{
      role_id: string;
      weight: number;
      overall_score: number;
      severity: string;
      urgency: string;
    }>;
  };
}
```

## 評価システムのアーキテクチャ

### マルチ視点評価システム

Helmは、ルールベース分析とマルチ視点LLM分析を組み合わせたアンサンブル評価システムを採用しています。

#### 1. ルールベース分析

定量的な指標に基づいて構造的問題を検知します：

- **KPI下方修正回数**: 会議内でKPIの下方修正が何回言及されたか
- **撤退議論の有無**: 撤退やピボットの議論が行われたか
- **判断集中率**: 最も多く発言した人の発言数 / 総発言数
- **反対意見の無視**: チャットで反対意見が出ているが、会議で反映されていない

これらの指標から、以下のパターンを検出します：

- **B1_正当化フェーズ**: KPI下方修正が2回以上、撤退議論なし、判断集中率40%以上
- **ES1_報告遅延**: リスク提起メッセージあり、エスカレーション未完了

#### 2. マルチ視点LLM分析

同じ会議ログとチャットログを、4つの異なる視点からLLM（Gemini）で評価します：

- **Executive視点（重み: 0.4）**: 全社の業績・リスク・ステークホルダー責任の観点
- **Corp Planning視点（重み: 0.3）**: KPI・事業ポートフォリオ・撤退/投資判断の観点
- **Staff視点（重み: 0.2）**: 実行可能性と現場負荷の観点
- **Governance視点（重み: 0.1）**: 報告遅延・隠れたリスク・コンプライアンスの観点

各ロールは専用のプロンプトを使用し、それぞれの立場から構造的リスクを評価します。

#### 3. アンサンブルスコアリング

ルールベース分析結果とマルチ視点LLM分析結果を統合します：

- **スコア計算**: `最終スコア = 0.6 × ルールベーススコア + 0.4 × LLM平均スコア`
- **重要度・緊急度**: ルールベースと各ロールの結果のうち、最も強い（安全側）を採用
- **説明文**: ルールベースの説明 + 主要ロール（Executive, Corp Planning）のコメント

このアプローチにより、単一の評価軸では見落としがちな問題も、複数の視点から検知できるようになります。

## パターン検出ロジック

### B1_正当化フェーズ

**検出条件（ルールベース）:**
- KPI下方修正が2回以上
- 撤退/ピボット議論が一度も行われていない
- 判断集中率が40%以上

**スコア計算:**
- ルールベース基本スコア: 75点（閾値: 70点）
- LLM評価: 各ロールが独自に評価（通常70-85点）
- アンサンブル後: ルールベースとLLMの重み付き平均

**説明:**
「現在の会議構造は「正当化フェーズ」に入っています。数値悪化は共有されていますが、戦略変更を提案する主体と「やめる」という選択肢が構造的に排除されています。」

### ES1_報告遅延

**検出条件（ルールベース）:**
- リスク提起メッセージが存在
- エスカレーション未完了
- 判断集中率が50%未満

**スコア計算:**
- ルールベース基本スコア: 65点（閾値: 40点）
- LLM評価: 各ロールが独自に評価（特にGovernance視点が強く検出）
- アンサンブル後: ルールベースとLLMの重み付き平均

### A2_撤退判断の遅れ

**検出条件（主にLLM検出）:**
- DX事業の営業利益率が悪化しているにも関わらず、撤退やピボットの議論が行われていない
- チャットログから現場レベルでの問題意識が示唆される

**スコア計算:**
- LLM評価: 各ロールが独自に評価（通常60-70点）
- アンサンブル後: LLM評価が主要な要素となる

## デプロイアーキテクチャ

### 開発環境

```
┌─────────────┐         ┌─────────────┐
│  Frontend   │ ──────▶ │  Backend    │
│ localhost:  │         │ localhost:  │
│    3000     │         │    8000     │
└─────────────┘         └─────────────┘
```

### 本番環境（将来）

```
┌─────────────────┐
│  Firebase       │
│  Hosting        │  (Frontend)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Cloud Run      │  (Backend API)
└────────┬────────┘
         │
         ├──▶ Firestore (データ保存)
         ├──▶ Vertex AI (AI分析)
         └──▶ Google APIs (各種サービス)
```

## 定義ドキュメント（組織グラフ・RACI・承認フロー）

組織グラフ・RACI・承認フローを JSON で管理し、EscalationEngine と approve に組み込んでいます。

- **配置**: `backend/config/definitions/`（org_graph.json, raci.json, approval_flows.json）。のちに Firestore 優先読み込みに対応可能。
- **DefinitionLoader**: 3 種の定義をファイル（または Firestore）から読み返す。
- **ResponsibilityResolver**: 分析結果の pattern_id から RACI の R（責任者）と承認フローの flow_id を解決。EscalationEngine に注入し、create_escalation の返却に target_roles / approval_flow_id を含める。
- **ApprovalFlowEngine**: テンプレートに基づく多段階承認（ステージ遷移・全員承認判定）。approve API は approval_flow_id がある場合にフローエンジンで処理し、完了時のみ approval レコードを作成。
- **定義がない場合**: 従来どおり「常に Executive」「1 回の approve で完了」にフォールバック。

## セキュリティ

### 認証・認可

**現在の実装:**
- **API Key 認証（オプション）**: 環境変数 `API_KEYS` に JSON 配列（例: `[{"key":"xxx","role":"owner"}]`）を設定すると、`/`・`/docs` 以外のパスで `X-API-Key` ヘッダ必須。無いと 401、不正キーで 403。キーに紐づくロールは監査ログ・承認フローで利用。詳細は [認証設計](./docs/auth-api-key-roles.md)。
- `API_KEYS` が空のときは認証不要（従来どおり）。
- CORS 設定により、指定されたオリジンのみアクセス可能。

**将来実装予定:**
- Google OAuth2 認証
- ルート別の必要ロール（例: `/api/admin/*` は admin のみ）

### データ保護

- 環境変数による機密情報管理（`.env`ファイル）
- HTTPS通信（本番環境）
- CORS設定（`config.py`で設定）
- エラーログに機密情報を含めない

## 拡張性

### 追加可能な機能

1. **新しいパターン検出**
   - `analyzer.py` に新しいパターンロジックを追加

2. **新しい情報源**
   - `services/` に新しいサービスを追加
   - 例: `google_docs.py`, `google_sheets.py`

3. **新しい実行タスク**
   - `main.py` の `execute` エンドポイントを拡張

4. **新しいUI画面**
   - `app/demo/` に新しいケースを追加

## パフォーマンス

### 最適化ポイント

1. **キャッシング**
   - 分析結果のキャッシュ
   - 議事録パース結果のキャッシュ

2. **非同期処理**
   - バックグラウンドタスク実行
   - タスクキュー（Celery等）

3. **データベース最適化**
   - Firestoreインデックス設定
   - クエリ最適化

## 監視・ログ

### ログ機能

**実装済み:**
- 構造化ログ（JSON形式）
- リクエストID追跡（各リクエストに一意のIDを付与）
- エラーログの詳細記録（スタックトレース含む）
- エラー通知機能（`error_notifier.py`）

**ログレベル:**
- INFO: 通常の処理ログ
- WARNING: 警告（API接続失敗等）
- ERROR: エラー（例外発生等）

**ログ出力先:**
- 標準出力（開発環境）
- ファイル出力（将来実装予定）
- Cloud Logging（本番環境、将来実装予定）

### メトリクス（将来実装予定）

- APIレスポンス時間
- エラー率
- 分析実行時間
- タスク実行時間
- LLM API呼び出し回数・成功率

## 最新の実装状況

### 実装済み機能

- ✅ **マルチ視点評価システム**
  - ルールベース分析（定量的指標に基づく検知）
  - マルチ視点LLM分析（4つのロール視点から評価）
  - アンサンブルスコアリング（統合評価）
- ✅ LLM統合（Gemini / Gen AI SDK）
  - 構造的問題検知（マルチ視点LLM分析）
  - タスク生成（LLM生成）
  - ロール別プロンプト生成
  - モックフォールバック
- ✅ エラーハンドリングの改善
  - カスタム例外クラス
  - エラーID追跡
  - ユーザーフレンドリーなエラーメッセージ
- ✅ ログ機能の強化
  - 構造化ログ
  - リクエストID追跡
  - エラー通知
- ✅ 出力サービス
  - 分析結果のJSONファイル保存
  - タスク生成結果のJSONファイル保存
- ✅ WebSocket統合
  - 実行進捗のリアルタイム更新
- ✅ 新規エンドポイント
  - `/api/materials/ingest` - 資料取り込み
  - `/api/download/{file_id}` - ファイルダウンロード
  - `/api/outputs` - 出力ファイル一覧
  - `/api/outputs/{file_id}` - 出力ファイル取得
  - `/api/feedback/false-positive` - 誤検知フィードバック
  - `/api/metrics/accuracy` - 精度指標取得
  - `/api/audit/logs` - 監査ログ取得
  - `/api/admin/retention/cleanup` - データ保存期間に基づく削除
- ✅ **認証（API Key ＋ ロール）**: `API_KEYS` で有効化、`X-API-Key` 検証。オーナーキー例は backend README 参照。
- ✅ **取得範囲ホワイトリスト・サプレッション**: 会議/チャットIDのホワイトリスト、検知のサプレッション条件（config）。
- ✅ **データ保存期間**: 保持日数設定と定期削除 API。設計は [data-retention.md](./docs/data-retention.md)。
- ✅ **冪等性（execute）**: 同一 approval_id の再リクエストは既存実行を返す。設計は [idempotency-execute.md](./docs/idempotency-execute.md)。
- ✅ **定義ドキュメント駆動**: 組織グラフ・RACI・承認フローを JSON で管理。DefinitionLoader、ResponsibilityResolver、ApprovalFlowEngine。多段階承認（テンプレートに基づくステージ遷移）をサポート。
- ✅ **将来実装の設計ドキュメント**: [docs/future/](./docs/future/) に ownership-model, multi-tenancy, job-queue, notification-policy を設計のみで記載。

### 将来実装予定

- ⏳ Firestore 統合（データの永続化、定義の Firestore 優先読み込み）
- ⏳ ルート別の必要ロール（admin 専用 API 等）
- ⏳ レート制限
- ⏳ メトリクス収集
- ⏳ バックグラウンドタスクキュー（Celery / Cloud Tasks 等）

## 参考資料

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [Next.js公式ドキュメント](https://nextjs.org/docs)
- [Google Cloud API](https://cloud.google.com/apis)
- [Vertex AI](https://cloud.google.com/vertex-ai)
- [APIドキュメント](./backend/API_DOCUMENTATION.md)
- [開発者ガイド](./DEVELOPER_GUIDE.md)

