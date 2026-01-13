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

### 4. AI自律実行フロー

```
[承認完了]
      │
      ▼
[実行計画生成]
      │
      ├─→ [タスク1: 市場データ分析]
      ├─→ [タスク2: 社内データ統合]
      ├─→ [タスク3: 資料生成]
      ├─→ [タスク4: 通知送信]
      └─→ [タスク5: 会議設定]
      │
      ▼
[Google Workspace API]
      │
      ├─→ [リサーチ]
      ├─→ [分析]
      ├─→ [資料作成]
      └─→ [通知]
      │
      ▼
[Google Drive API]
      │
      ▼
[結果保存 & ダウンロードURL生成]
      │
      ▼
[フロントエンドに結果返却]
```

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
├── services/               # サービス層
│   ├── google_meet.py      # Google Meet統合
│   ├── google_chat.py      # Google Chat統合
│   ├── analyzer.py         # 構造的問題検知（ルールベース）
│   ├── multi_view_analyzer.py  # マルチ視点LLM分析
│   ├── ensemble_scoring.py     # アンサンブルスコアリング
│   ├── llm_service.py      # LLM統合サービス（Gemini / Gen AI SDK）
│   ├── scoring.py          # スコアリングサービス
│   ├── escalation_engine.py # エスカレーション判断エンジン
│   ├── google_workspace.py # Google Workspace統合
│   ├── google_drive.py     # Google Drive統合
│   ├── output_service.py   # 出力サービス
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

## セキュリティ

### 認証・認可

**現在の実装:**
- 認証不要（開発環境）
- CORS設定により、指定されたオリジンのみアクセス可能

**将来実装予定:**
- Google OAuth2認証
- サービスアカウント認証
- ロールベースアクセス制御

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

### 将来実装予定

- ⏳ Firestore統合（データの永続化）
- ⏳ 認証・認可機能
- ⏳ レート制限
- ⏳ メトリクス収集
- ⏳ バックグラウンドタスクキュー（Celery等）

## 参考資料

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [Next.js公式ドキュメント](https://nextjs.org/docs)
- [Google Cloud API](https://cloud.google.com/apis)
- [Vertex AI](https://cloud.google.com/vertex-ai)
- [APIドキュメント](./backend/API_DOCUMENTATION.md)
- [開発者ガイド](./DEVELOPER_GUIDE.md)

