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
│  │  │  Structure   │  │  Vertex AI   │                │   │
│  │  │   Analyzer   │  │   Service    │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
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

### 2. 構造的問題検知フロー

```
[構造化データ]
      │
      ▼
[Structure Analyzer]
      │
      ├─→ [ルールベース分析] (現在)
      └─→ [Vertex AI分析] (将来)
      │
      ▼
[パターン検出]
      │
      ├─→ B1_正当化フェーズ
      ├─→ ES1_報告遅延
      └─→ その他のパターン
      │
      ▼
[スコアリング & 説明生成]
      │
      ▼
[アラート生成]
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
├── services/               # サービス層
│   ├── google_meet.py      # Google Meet統合
│   ├── google_chat.py      # Google Chat統合
│   ├── analyzer.py         # 構造的問題検知
│   ├── vertex_ai.py        # Vertex AI統合
│   ├── google_workspace.py # Google Workspace統合
│   └── google_drive.py     # Google Drive統合
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

**StructureAnalyzer**
- ルールベース分析（現在）
- Vertex AI分析（将来）
- パターン検出とスコアリング

**GoogleWorkspaceService**
- 市場データリサーチ
- データ分析
- 資料生成
- 通知送信

**GoogleDriveService**
- ファイル保存
- ダウンロードURL生成
- ファイル共有

## API設計

### エンドポイント一覧

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| POST | `/api/meetings/ingest` | 議事録取り込み |
| POST | `/api/chat/ingest` | チャット取り込み |
| POST | `/api/analyze` | 構造的問題検知 |
| GET | `/api/analysis/{id}` | 分析結果取得 |
| POST | `/api/escalate` | Executive呼び出し |
| POST | `/api/approve` | Executive承認 |
| POST | `/api/execute` | AI自律実行開始 |
| GET | `/api/execution/{id}` | 実行状態取得 |
| GET | `/api/execution/{id}/results` | 実行結果取得 |

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
  }>;
  score: number;
  severity: string;
  explanation: string;
  created_at: string;
}
```

## パターン検出ロジック

### B1_正当化フェーズ

**検出条件:**
- KPI下方修正が2回以上
- 撤退/ピボット議論が一度も行われていない
- 判断集中率が70%以上

**スコア計算:**
- 基本スコア: 75点
- 閾値: 70点

**説明:**
「現在の会議構造は「正当化フェーズ」に入っています。数値悪化は共有されていますが、戦略変更を提案する主体と「やめる」という選択肢が構造的に排除されています。」

### ES1_報告遅延

**検出条件:**
- リスク提起メッセージが存在
- エスカレーション未完了
- 判断集中率が50%未満

**スコア計算:**
- 基本スコア: 65点
- 閾値: 40点

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

### 認証・認可（将来実装）

- Google OAuth2認証
- サービスアカウント認証
- ロールベースアクセス制御

### データ保護

- 環境変数による機密情報管理
- HTTPS通信
- CORS設定

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

### ログレベル

- INFO: 通常の処理ログ
- WARNING: 警告（API接続失敗等）
- ERROR: エラー（例外発生等）

### メトリクス（将来）

- APIレスポンス時間
- エラー率
- 分析実行時間
- タスク実行時間

## 参考資料

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [Next.js公式ドキュメント](https://nextjs.org/docs)
- [Google Cloud API](https://cloud.google.com/apis)
- [Vertex AI](https://cloud.google.com/vertex-ai)

