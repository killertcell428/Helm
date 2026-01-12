# Helm Backend API ドキュメント

## ベースURL

- 開発環境: `http://localhost:8000`
- 本番環境: `https://helm-api-xxxxx-xx.a.run.app` (将来)

## 認証

現在は認証不要です。将来はGoogle OAuth2を使用予定。

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

---

### 4. 構造的問題検知

**POST /api/analyze**

会議データとチャットデータから構造的問題を検知します。

**リクエストボディ:**
```json
{
  "meeting_id": "meeting_001",
  "chat_id": "chat_001"  // オプション
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
  "score": 75,
  "severity": "HIGH",
  "explanation": "現在の会議構造は「正当化フェーズ」に入っています...",
  "created_at": "2025-01-20T10:00:00",
  "status": "completed"
}
```

---

### 5. 分析結果取得

**GET /api/analysis/{analysis_id}**

分析結果の詳細を取得します。

**パスパラメータ:**
- `analysis_id`: 分析ID

**レスポンス:**
上記の `/api/analyze` と同じ形式

---

### 6. Executive呼び出し

**POST /api/escalate**

構造的問題が検出された場合、Executiveを呼び出します。

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
  "reason": "正当化フェーズの兆候が検出されました。構造的変更にはExecutiveの承認が必要です。",
  "created_at": "2025-01-20T10:05:00",
  "status": "pending"
}
```

---

### 7. Executive承認

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

---

### 8. AI自律実行開始

**POST /api/execute**

Executive承認後、AIが自律的にタスクを実行します。

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
  "updated_at": "2025-01-20T10:15:00"
}
```

---

### 9. 実行状態取得

**GET /api/execution/{execution_id}**

AI自律実行の進捗状況を取得します。

**パスパラメータ:**
- `execution_id`: 実行ID

**レスポンス:**
上記の `/api/execute` と同じ形式（`status` と `progress` が更新される）

---

### 10. 実行結果取得

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

## エラーレスポンス

すべてのエンドポイントで、エラーが発生した場合は以下の形式で返されます：

```json
{
  "detail": "エラーメッセージ"
}
```

**HTTPステータスコード:**
- `200`: 成功
- `404`: リソースが見つからない
- `500`: サーバーエラー

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

# 構造的問題検知
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

## インタラクティブAPIドキュメント

開発サーバー起動後、以下のURLでSwagger UIが利用できます：

http://localhost:8000/docs

ここで全エンドポイントの詳細を確認し、実際にAPIを呼び出すことができます。

