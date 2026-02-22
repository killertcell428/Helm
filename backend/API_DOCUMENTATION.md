# Helm Backend API ドキュメント

## ベースURL

- 開発環境: `http://localhost:8000`
- 本番環境: `https://helm-api-xxxxx-xx.a.run.app` (将来)

## 認証

- **オフ（デフォルト）**: 環境変数 `API_KEYS` が未設定または空のときは認証不要。従来どおり全エンドポイントにアクセス可能。
- **オン**: `API_KEYS` に JSON 配列（例: `[{"key":"helm-owner-dev-key","role":"owner"}]`）を設定すると、`/`・`/docs`・`/redoc`・`/openapi.json` 以外では **`X-API-Key` ヘッダ必須**。キーなし → 401、不正なキー → 403。詳細は [認証設計](../docs/auth-api-key-roles.md) を参照。

## インタラクティブAPIドキュメント

開発サーバー起動後、以下のURLでSwagger UIが利用できます：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

ここで全エンドポイントの詳細を確認し、実際にAPIを呼び出すことができます。

## エンドポイント

### 1. ヘルスチェック

**GET /** 

APIの動作確認用エンドポイント。

**レスポンス:**
```json
{
  "message": "Helm API",
  "version": "0.1.0",
  "status": "running"
}
```

---

### 2. 議事録取り込み

**POST /api/meetings/ingest**

Google Meet議事録を取り込み、パース処理を実行します。

**リクエストボディ:**
```json
{
  "meeting_id": "meeting_001",
  "transcript": "CFO: 今期の成長率は計画を下回っています...",  // オプション
  "metadata": {
    "meeting_name": "四半期経営会議",
    "date": "2025-01-15",
    "participants": ["CFO", "CEO", "通信本部長", "DX本部長"]
  }
}
```

**レスポンス:**
```json
{
  "meeting_id": "meeting_001",
  "status": "success",
  "parsed": {
    "statements": [
      {
        "speaker": "CFO",
        "text": "今期の成長率は計画を下回っています..."
      }
    ],
    "kpi_mentions": [...],
    "exit_discussed": false,
    "total_statements": 10
  }
}
```

**注意:**
- `transcript` が空または未指定の場合、Google Meet APIから自動取得します（現在はモックデータ）
- レスポンスには実際の議事録テキスト（`transcript`）とメタデータ（`metadata`）も含まれます

**エラーレスポンス:**
- `503 Service Unavailable`: Google Meet APIからの取得に失敗した場合
- `422 Validation Error`: リクエストボディのバリデーションエラー

---

### 3. チャット取り込み

**POST /api/chat/ingest**

Google Chatログを取り込み、パース処理を実行します。

**リクエストボディ:**
```json
{
  "chat_id": "chat_001",
  "messages": [  // オプション
    {
      "user": "経営企画A",
      "text": "数字かなり厳しかったですね…",
      "timestamp": "2025-01-15T15:30:00Z"
    }
  ],
  "metadata": {
    "channel_name": "経営企画チャンネル",
    "project_id": "project_zombie"
  }
}
```

**レスポンス:**
```json
{
  "chat_id": "chat_001",
  "status": "success",
  "parsed": {
    "total_messages": 3,
    "risk_messages": [...],
    "escalation_mentioned": false,
    "opposition_messages": [...],
    "has_concern": true
  }
}
```

**注意:**
- `messages` が空または未指定の場合、Google Chat APIから自動取得します（現在はモックデータ）
- レスポンスには実際のチャットメッセージ（`messages`）とメタデータ（`metadata`）も含まれます

**エラーレスポンス:**
- `503 Service Unavailable`: Google Chat APIからの取得に失敗した場合
- `422 Validation Error`: リクエストボディのバリデーションエラー

---

### 4. 資料取り込み

**POST /api/materials/ingest**

会議資料（スライド、ドキュメントなど）を取り込みます。

**リクエストボディ:**
```json
{
  "material_id": "material_001",
  "content": "会議資料のテキスト内容...",
  "metadata": {
    "title": "四半期経営会議資料",
    "type": "presentation",
    "created_at": "2025-01-15T10:00:00Z"
  }
}
```

**レスポンス:**
```json
{
  "material_id": "material_001",
  "status": "success",
  "content_length": 1234,
  "metadata": {
    "title": "四半期経営会議資料",
    "type": "presentation",
    "created_at": "2025-01-15T10:00:00Z"
  }
}
```

**注意:**
- 資料のテキスト内容を`content`フィールドに含める必要があります
- 意思決定の詰まりの検知時に`material_id`を指定することで、資料内容も分析に含まれます

**エラーレスポンス:**
- `422 Validation Error`: リクエストボディのバリデーションエラー

---

### 5. 意思決定の詰まりの検知

**POST /api/analyze**

会議データとチャットデータから意思決定の詰まり（判断の遅れ・責任の曖昧さ等）を検知します。**マルチ視点評価システム**により、ルールベース分析とマルチ視点LLM分析（4つのロール視点）をアンサンブルして、より精度の高い評価を実現します。

**リクエストボディ:**
```json
{
  "meeting_id": "meeting_001",
  "chat_id": "chat_001",  // オプション
  "material_id": "material_001"  // オプション（会議資料）
}
```

**レスポンス:**
```json
{
  "analysis_id": "analysis_123",
  "meeting_id": "meeting_001",
  "chat_id": "chat_001",
  "findings": [
    {
      "pattern_id": "B1_正当化フェーズ",
      "severity": "HIGH",
      "score": 75,
      "description": "KPI悪化認識があるが戦略変更議論がない",
      "evidence": [
        "KPI下方修正が3回検出",
        "撤退/ピボット議論が一度も行われていない",
        "判断集中率: 75.00%"
      ],
      "quantitative_scores": {
        "kpi_downgrade_count": 3,
        "exit_discussed": false,
        "decision_concentration_rate": 0.75,
        "ignored_opposition_count": 2
      }
    }
  ],
  "scores": {
    "B1_正当化フェーズ": 75
  },
  "score": 69,
  "severity": "HIGH",
  "urgency": "HIGH",
  "explanation": "【重要度: MEDIUM / 緊急度: HIGH】\n\nリスク認識から報告までの遅延が検出されました...",
  "created_at": "2025-01-20T10:00:00",
  "status": "completed",
  "is_llm_generated": true,
  "llm_status": "success",
  "llm_model": "models/gemini-1.5-flash",
  "multi_view": [
    {
      "role_id": "executive",
      "weight": 0.4,
      "overall_score": 75,
      "severity": "HIGH",
      "urgency": "MEDIUM",
      "explanation": "KPI悪化が継続しているにも関わらず、計画維持の意思決定がなされており...",
      "analysis": { ... }
    },
    {
      "role_id": "corp_planning",
      "weight": 0.3,
      "overall_score": 75,
      "severity": "HIGH",
      "urgency": "HIGH",
      "explanation": "KPI悪化にも関わらず計画維持の決定は、判断が止まっているリスクを示唆します...",
      "analysis": { ... }
    },
    {
      "role_id": "staff",
      "weight": 0.2,
      "overall_score": 75,
      "severity": "HIGH",
      "urgency": "HIGH",
      "explanation": "KPIの悪化が続いているにも関わらず、計画の維持が決定され...",
      "analysis": { ... }
    },
    {
      "role_id": "governance",
      "weight": 0.1,
      "overall_score": 75,
      "severity": "HIGH",
      "urgency": "MEDIUM",
      "explanation": "KPI悪化が継続しているにも関わらず、現状維持の判断が優先されています...",
      "analysis": { ... }
    }
  ],
  "ensemble": {
    "overall_score": 69,
    "severity": "HIGH",
    "urgency": "HIGH",
    "reasons": [
      "【重要度: MEDIUM / 緊急度: HIGH】\n\nリスク認識から報告までの遅延が検出されました...",
      "[executive] KPI悪化が継続しているにも関わらず、計画維持の意思決定がなされており...",
      "[corp_planning] KPI悪化にも関わらず計画維持の決定は、判断が止まっているリスクを示唆します..."
    ],
    "contributing_roles": [
      {
        "role_id": "executive",
        "weight": 0.4,
        "overall_score": 75,
        "severity": "HIGH",
        "urgency": "MEDIUM"
      },
      {
        "role_id": "corp_planning",
        "weight": 0.3,
        "overall_score": 75,
        "severity": "HIGH",
        "urgency": "HIGH"
      },
      {
        "role_id": "staff",
        "weight": 0.2,
        "overall_score": 75,
        "severity": "HIGH",
        "urgency": "HIGH"
      },
      {
        "role_id": "governance",
        "weight": 0.1,
        "overall_score": 75,
        "severity": "HIGH",
        "urgency": "MEDIUM"
      }
    ]
  },
  "output_file": {
    "filename": "analysis_123.json",
    "file_id": "analysis_123",
    "path": "outputs/analysis_123.json"
  }
}
```

**レスポンスフィールドの説明:**
- `score`: アンサンブル後の最終スコア（0-100点）。`0.6 × ルールベーススコア + 0.4 × LLM平均スコア`で計算
- `severity`, `urgency`: ルールベースと各ロールの結果のうち、最も強い（安全側）を採用
- `is_llm_generated`: マルチ視点LLM分析が実行されたかどうか（`true`/`false`）
- `llm_status`: LLMの状態（`success`, `disabled`, `error`など）
- `llm_model`: 使用されたLLMモデル名（例: `models/gemini-1.5-flash`）
- `multi_view`: マルチ視点LLM分析の結果。4つのロール（Executive, Corp Planning, Staff, Governance）の評価結果を含む
  - `role_id`: ロールID
  - `weight`: ロールの重み（アンサンブル時に使用）
  - `overall_score`: そのロール視点でのスコア（0-100点）
  - `severity`, `urgency`: そのロール視点での重要度・緊急度
  - `explanation`: そのロール視点での説明文
  - `analysis`: そのロール視点での完全な分析結果（`findings`を含む）
- `ensemble`: アンサンブルスコアリングの結果
  - `overall_score`: アンサンブル後の最終スコア
  - `severity`, `urgency`: アンサンブル後の重要度・緊急度
  - `reasons`: 統合された理由文（ルールベース + 主要ロールのコメント）
  - `contributing_roles`: 各ロールの貢献度情報
- `output_file`: 分析結果が保存されたファイル情報（オプション）

**評価システムの動作:**
1. **ルールベース分析**: 定量的指標（KPI下方修正回数、撤退議論の有無、判断集中率など）に基づいて意思決定の詰まりを検知
2. **マルチ視点LLM分析**: 同じデータを4つの異なる視点（Executive, Corp Planning, Staff, Governance）からLLMで評価
3. **アンサンブルスコアリング**: ルールベース結果とLLM結果を統合して最終スコアを決定

**注意:**
- `chat_id`と`material_id`はオプションです
- LLM統合が無効な場合（`USE_LLM=false` または `GOOGLE_API_KEY`未設定）、ルールベース分析のみが実行されます（`multi_view`は空配列）
- 分析結果は自動的にJSONファイルとして保存されます（`outputs/`ディレクトリ）

**エラーレスポンス:**
- `404 Not Found`: 指定された`meeting_id`が見つからない場合
- `503 Service Unavailable`: LLM分析に失敗した場合（ルールベース分析にフォールバック）
- `422 Validation Error`: リクエストボディのバリデーションエラー

---

### 6. 分析結果取得

**GET /api/analysis/{analysis_id}**

分析結果の詳細を取得します。

**パスパラメータ:**
- `analysis_id`: 分析ID

**レスポンス:**
上記の `/api/analyze` と同じ形式

**エラーレスポンス:**
- `404 Not Found`: 指定された`analysis_id`が見つからない場合

---

### 7. Executive呼び出し

**POST /api/escalate**

意思決定の詰まりが検出された場合、Executiveを呼び出します。

**リクエストボディ:**
```json
{
  "analysis_id": "analysis_123"
}
```

**レスポンス:**
```json
{
  "escalation_id": "escalation_456",
  "analysis_id": "analysis_123",
  "target_role": "Executive",
  "reason": "正当化フェーズの兆候が検出されました。方針変更にはExecutiveの承認が必要です。",
  "severity": "HIGH",
  "urgency": "MEDIUM",
  "score": 75,
  "created_at": "2025-01-20T10:05:00",
  "status": "pending"
}
```

**注意:**
- エスカレーション判断エンジンが、分析結果に基づいて自動的に適切なロールを決定します
- エスカレーション条件を満たしていない場合（スコアが閾値未満など）、エラーが返されます

**エラーレスポンス:**
- `404 Not Found`: 指定された`analysis_id`が見つからない場合
- `422 Validation Error`: エスカレーション条件を満たしていない場合

---

### 8. Executive承認

**POST /api/approve**

Executiveが介入案を承認または修正します。

**リクエストボディ:**
```json
{
  "escalation_id": "escalation_456",
  "decision": "approve",  // "approve" または "modify"
  "modifications": {  // オプション（decisionが"modify"の場合）
    "additional_conditions": "..."
  }
}
```

**レスポンス:**
```json
{
  "approval_id": "approval_789",
  "escalation_id": "escalation_456",
  "decision": "approve",
  "modifications": null,
  "created_at": "2025-01-20T10:10:00",
  "status": "approved"
}
```

**注意:**
- `decision`は`"approve"`または`"modify"`のいずれかである必要があります
- `modifications`は`decision`が`"modify"`の場合に使用されます

**エラーレスポンス:**
- `404 Not Found`: 指定された`escalation_id`が見つからない場合
- `422 Validation Error`: `decision`が無効な値の場合

---

### 9. AI自律実行開始（ADKベースのマルチエージェントシステム）

**POST /api/execute**

Executive承認後、AIが**ADK (Agent Development Kit)** を使用したマルチエージェントシステムで自律的にタスクを実行します。

**Phase1（実装完了）**: モック実装とADK統合、フォールバック対応
**Phase2（実装予定）**: 実際のAPI統合（Vertex AI Search、Google Drive、Google Chat/Gmail API）

**リクエストボディ:**
```json
{
  "approval_id": "approval_789"
}
```

**レスポンス:**
```json
{
  "execution_id": "execution_abc",
  "approval_id": "approval_789",
  "status": "running",
  "progress": 0,
  "tasks": [
    {
      "id": "task1",
      "name": "市場データ分析",
      "status": "pending",
      "type": "research"
    },
    {
      "id": "task2",
      "name": "社内データ統合",
      "status": "pending",
      "type": "analysis"
    },
    {
      "id": "task3",
      "name": "3案比較資料の自動生成",
      "status": "pending",
      "type": "document"
    },
    {
      "id": "task4",
      "name": "関係部署への事前通知",
      "status": "pending",
      "type": "notification"
    },
    {
      "id": "task5",
      "name": "会議アジェンダの更新",
      "status": "pending",
      "type": "calendar"
    }
  ],
  "created_at": "2025-01-20T10:15:00",
  "updated_at": "2025-01-20T10:15:00",
  "is_llm_generated": true,
  "llm_status": "success",
  "llm_model": "gemini-1.5-pro",
  "output_file": {
    "filename": "execution_abc_tasks.json",
    "file_id": "execution_abc",
    "path": "outputs/execution_abc_tasks.json"
  }
}
```

**レスポンスフィールドの説明:**
- `is_llm_generated`: タスク生成にLLMを使用したかどうか
- `llm_status`: LLMの状態
- `llm_model`: 使用されたLLMモデル名
- `output_file`: タスク生成結果が保存されたファイル情報（オプション）

**注意:**
- 実行はバックグラウンドで非同期に実行されます
- 実行進捗はWebSocketエンドポイント（`/api/execution/{execution_id}/ws`）でリアルタイムに取得できます
- タスク生成結果は自動的にJSONファイルとして保存されます

**エラーレスポンス:**
- `404 Not Found`: 指定された`approval_id`が見つからない場合
- `503 Service Unavailable`: LLMタスク生成に失敗した場合（モックタスクにフォールバック）

---

### 10. 実行状態取得

**GET /api/execution/{execution_id}**

AI自律実行の進捗状況を取得します。

**パスパラメータ:**
- `execution_id`: 実行ID

**レスポンス:**
上記の `/api/execute` と同じ形式（`status` と `progress` が更新される）

**注意:**
- 実行中のタスクは、経過時間に基づいて自動的に進捗が更新されます
- 各タスクは約2秒間隔で順次実行されます

**エラーレスポンス:**
- `404 Not Found`: 指定された`execution_id`が見つからない場合

---

### 11. 実行結果取得

**GET /api/execution/{execution_id}/results**

AI自律実行の結果を取得します。

**パスパラメータ:**
- `execution_id`: 実行ID

**レスポンス:**
```json
{
  "execution_id": "execution_abc",
  "results": [
    {
      "type": "document",
      "name": "3案比較資料の自動生成",
      "download_url": "https://drive.google.com/file/d/mock_file_id/view"
    },
    {
      "type": "notification",
      "name": "関係部署への事前通知",
      "recipients": 8
    },
    {
      "type": "research",
      "name": "市場データ分析",
      "data": {
        "topic": "ARPU動向",
        "results": [...]
      }
    }
  ],
  "download_url": "https://drive.google.com/file/d/mock_file_id/view"
}
```

**レスポンスフィールドの説明:**
- `results`: 完了したタスクの結果リスト
  - `type`: タスクタイプ（`document`, `notification`, `research`, `analysis`など）
  - `name`: タスク名
  - タスクタイプに応じた追加フィールド（`download_url`, `recipients`, `data`など）
- `download_url`: メインのダウンロードURL（最初のドキュメント）

**エラーレスポンス:**
- `404 Not Found`: 指定された`execution_id`が見つからない場合

---

### 12. WebSocket: 実行進捗のリアルタイム更新

**WebSocket /api/execution/{execution_id}/ws**

AI自律実行の進捗をリアルタイムで取得します。

**接続方法:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/execution/execution_abc/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
  // {
  //   "type": "progress",
  //   "data": {
  //     "execution_id": "execution_abc",
  //     "status": "running",
  //     "progress": 40,
  //     "tasks": [...]
  //   }
  // }
};
```

**メッセージタイプ:**
- `progress`: 進捗更新
- `completed`: 実行完了
- `error`: エラー発生

**注意:**
- WebSocket接続は実行中のみ有効です
- 複数のクライアントが同じ実行IDに接続できます

---

### 13. ファイルダウンロードURL取得

**GET /api/download/{file_id}**

Google DriveファイルのダウンロードURLを取得します。

**パスパラメータ:**
- `file_id`: Google DriveファイルID

**レスポンス:**
```json
{
  "file_id": "mock_file_id",
  "download_url": "https://drive.google.com/file/d/mock_file_id/view",
  "filename": "3案比較資料.pdf"
}
```

**エラーレスポンス:**
- `404 Not Found`: 指定された`file_id`が見つからない場合
- `503 Service Unavailable`: Google Drive APIからの取得に失敗した場合

---

### 14. 出力ファイル一覧取得

**GET /api/outputs**

保存された出力ファイルの一覧を取得します。

**クエリパラメータ:**
- `file_type` (オプション): ファイルタイプでフィルタ（例: `analysis`, `tasks`）

**レスポンス:**
```json
{
  "files": [
    {
      "filename": "analysis_123.json",
      "file_id": "analysis_123",
      "file_type": "analysis",
      "created_at": "2025-01-20T10:00:00",
      "size": 1234
    }
  ],
  "total": 1
}
```

**エラーレスポンス:**
- `500 Internal Server Error`: ファイル一覧の取得に失敗した場合

---

### 15. 出力ファイル取得

**GET /api/outputs/{file_id}**

保存された出力ファイルをダウンロードします。

**パスパラメータ:**
- `file_id`: ファイルID

**レスポンス:**
- `Content-Type`: `application/json`
- ファイルの内容（JSON形式）

**エラーレスポンス:**
- `404 Not Found`: 指定された`file_id`が見つからない場合

---

### 16. 誤検知フィードバック

**POST /api/feedback/false-positive**

精度改善のため、誤検知として登録します。

**リクエストボディ:**
```json
{
  "analysis_id": "analysis_001",
  "pattern_id": "B1_正当化フェーズ",
  "reason": "KPI下方修正は計画内の見直しであり意思決定の詰まりではない",
  "mitigation": null
}
```

**レスポンス:**
```json
{
  "false_positive_id": "1",
  "analysis_id": "analysis_001",
  "pattern_id": "B1_正当化フェーズ",
  "status": "registered"
}
```

---

### 17. 精度指標取得

**GET /api/metrics/accuracy**

Precision / Recall / F1 / 誤検知率を取得します。`pattern_id` でパターン別に絞り込み可能です。

**クエリパラメータ:**
- `pattern_id`（オプション）: パターンID（指定時はそのパターンのみ集計）

**レスポンス:**
```json
{
  "precision": 0.85,
  "recall": 0.9,
  "f1_score": 0.87,
  "false_positive_rate": 0.15,
  "true_positives": 9,
  "false_positives": 2,
  "false_negatives": 1,
  "total_labels": 12,
  "pattern_id": "B1_正当化フェーズ"
}
```

---

### 18. 監査ログ取得

**GET /api/audit/logs**

監査ログを取得します。クエリパラメータでフィルタ可能です。

**クエリパラメータ:**
- `user_id`, `role`, `action`, `resource_type`, `resource_id`（オプション）
- `start_time`, `end_time`（オプション・ISO8601形式）
- `limit`（オプション・デフォルト 100、最大 500）

**レスポンス:**
```json
{
  "logs": [
    {
      "log_id": "...",
      "timestamp": "2025-02-12T10:00:00",
      "user_id": "user1",
      "role": "owner",
      "action": "view_analysis",
      "resource_type": "analysis",
      "resource_id": "analysis_001",
      "details": {},
      "prev_hash": "...",
      "entry_hash": "..."
    }
  ],
  "count": 1
}
```

各エントリには改ざん検知用のハッシュチェーン（`prev_hash`, `entry_hash`）が付与されます。

---

### 19. 監査ログのハッシュチェーン検証

**GET /api/audit/verify**

監査ログのハッシュチェーンを検証し、改ざんの有無を返します。

**レスポンス:**
```json
{
  "valid": true,
  "invalid_index": null,
  "total_entries": 42,
  "message": "Chain verified successfully"
}
```

改ざんが検出された場合は `valid: false`、`invalid_index` に問題のインデックス、`message` に詳細が入ります。

---

### 20. 分析利用状況（メトリクス）取得

**GET /api/metrics/usage**

直近の分析の平均レイテンシ・トークン数・分析件数を取得します。

**クエリパラメータ:**
- `last_n`（オプション）: 直近 N 件に絞って集計。未指定時は全件。

**レスポンス:**
```json
{
  "count": 10,
  "avg_latency_ms": 3500.5,
  "total_llm_calls": 40,
  "total_input_tokens": 120000,
  "total_output_tokens": 8000,
  "total_tokens": 128000
}
```

---

### 21. データ保存期間に基づく削除（管理用）

**POST /api/admin/retention/cleanup**

設定された保持日数を超えたデータを各ストアから削除します。日次バッチ等から呼び出す想定です。

**レスポンス:**
```json
{
  "status": "ok",
  "deleted": {
    "executions_db": 0,
    "approvals_db": 0,
    "escalations_db": 0,
    "analyses_db": 0,
    "meetings_db": 0,
    "chats_db": 0,
    "materials_db": 0
  }
}
```

設計は [data-retention.md](../docs/data-retention.md) を参照。

---

## エラーレスポンス

すべてのエンドポイントで、エラーが発生した場合は以下の形式で返されます：

```json
{
  "error_id": "550e8400-e29b-41d4-a716-446655440000",
  "error_code": "NOT_FOUND",
  "message": "会議データが見つかりません: meeting_001",
  "details": {
    "resource_type": "meeting",
    "resource_id": "meeting_001"
  }
}
```

**エラーレスポンスフィールド:**
- `error_id`: エラーを一意に識別するID（トラブルシューティング用）
- `error_code`: エラーコード（下記参照）
- `message`: エラーメッセージ（日本語）
- `details`: エラーの詳細情報（オプション）

**HTTPステータスコード:**
- `200`: 成功
- `400`: バリデーションエラー（`VALIDATION_ERROR`）
- `401`: 認証が必要（API Key 有効時でキー未送信）
- `403`: 認可エラー（API Key 無効・不正）
- `404`: リソースが見つからない（`NOT_FOUND`）
- `429`: レート制限超過（`RATE_LIMIT_EXCEEDED`）。`Retry-After` ヘッダで再試行までの秒数を示す。
- `422`: リクエストボディのバリデーションエラー（`VALIDATION_ERROR`）
- `500`: 内部サーバーエラー（`INTERNAL_SERVER_ERROR`）
- `503`: サービス利用不可（`SERVICE_ERROR`）
- `504`: タイムアウト（`TIMEOUT_ERROR`）

**エラーコード一覧:**
- `VALIDATION_ERROR`: バリデーションエラー
- `NOT_FOUND`: リソースが見つからない
- `RATE_LIMIT_EXCEEDED`: レート制限超過（1分あたりのリクエスト数上限）
- `SERVICE_ERROR`: 外部サービス（Google APIなど）の呼び出しエラー
- `TIMEOUT_ERROR`: タイムアウトエラー
- `RETRYABLE_ERROR`: リトライ可能なエラー
- `INTERNAL_SERVER_ERROR`: 内部サーバーエラー
- `HTTP_{status_code}`: HTTP例外（例: `HTTP_404`）

**エラーハンドリングのベストプラクティス:**
1. `error_id`を記録しておくと、トラブルシューティングが容易になります
2. `error_code`に基づいて適切な処理を実装できます
3. `details`フィールドに追加情報が含まれる場合があります
4. `503 Service Unavailable`エラーの場合、リトライを検討してください

## 使用例

### cURL

```bash
# 議事録取り込み
curl -X POST http://localhost:8000/api/meetings/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_id": "meeting_001",
    "metadata": {
      "meeting_name": "四半期経営会議",
      "date": "2025-01-15",
      "participants": ["CFO", "CEO"]
    }
  }'

# 意思決定の詰まりの検知
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_id": "meeting_001",
    "chat_id": "chat_001"
  }'
```

### JavaScript (Fetch API)

```javascript
// 議事録取り込み
const response = await fetch('http://localhost:8000/api/meetings/ingest', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    meeting_id: 'meeting_001',
    metadata: {
      meeting_name: '四半期経営会議',
      date: '2025-01-15',
      participants: ['CFO', 'CEO']
    }
  })
});

const data = await response.json();
console.log(data);
```

## レート制限・制約事項

現在、レート制限は実装されていません。将来実装予定です。

**制約事項:**
- 議事録の最大サイズ: 制限なし（ただし、大きな議事録は処理に時間がかかる場合があります）
- チャットメッセージ数: 制限なし
- 同時実行数: 制限なし（ただし、リソースに応じて調整が必要な場合があります）

## データの永続化

現在、データはインメモリストレージに保存されています。サーバーを再起動するとデータは失われます。

**将来実装予定:**
- Firestore統合によるデータの永続化
- 分析結果の履歴管理
- エスカレーション履歴の永続化

## モックモードと実APIモード

Helmは、モックモードと実APIモードの両方をサポートしています。

**モックモード:**
- Google APIの認証情報が設定されていない場合、自動的にモックモードになります
- モックデータを使用して動作確認が可能です
- レスポンスに`is_llm_generated: false`、`llm_status: "mock_fallback"`が含まれます

**実APIモード:**
- Google Cloud認証情報が設定されている場合、実APIモードになります
- 実際のGoogle Meet、Google Chat、Vertex AI APIが使用されます
- レスポンスに`is_llm_generated: true`、`llm_status: "success"`が含まれます

**環境変数:**
- `USE_LLM=true`: LLM統合を有効化
- `GOOGLE_APPLICATION_CREDENTIALS`: Google Cloud認証情報のパス
- `GOOGLE_CLOUD_PROJECT_ID`: Google CloudプロジェクトID

詳細は[開発者ガイド](../DEVELOPER_GUIDE.md)を参照してください。

