# Googleサービス統合（モック）の確認方法

現在、Googleサービスはモックデータを使用して実装されています。以下の方法で動作を確認できます。

## 0. テストスクリプトを実行（推奨）

最も簡単な確認方法は、テストスクリプトを実行することです：

```bash
cd Dev/backend
pip install -r requirements_minimal.txt  # requestsが含まれています
python test_mock_services.py
```

これで4つのサービスすべてが自動的にテストされます。

## 1. APIエンドポイントを直接呼び出す

### Google Meetサービス（議事録取得）

**エンドポイント:** `POST /api/meetings/ingest`

**リクエスト例:**
```bash
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
```

**期待されるレスポンス:**
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
    "kpi_mentions": [
      {
        "type": "downgrade",
        "metric": "成長率",
        "value": "計画比-15%"
      }
    ],
    "exit_discussed": false,
    "total_statements": 10
  }
}
```

**確認ポイント:**
- ✅ `parsed.kpi_mentions` にKPI下方修正が含まれている
- ✅ `parsed.exit_discussed` が `false`（撤退議論がない）
- ✅ `parsed.statements` に発言者とテキストが含まれている

### Google Chatサービス（チャット取得）

**エンドポイント:** `POST /api/chat/ingest`

**リクエスト例:**
```bash
curl -X POST http://localhost:8000/api/chat/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "chat_001",
    "metadata": {
      "channel_name": "経営企画チャンネル",
      "project_id": "project_zombie"
    }
  }'
```

**期待されるレスポンス:**
```json
{
  "chat_id": "chat_001",
  "status": "success",
  "parsed": {
    "total_messages": 3,
    "risk_messages": [
      {
        "user": "経営企画A",
        "text": "数字かなり厳しかったですね…",
        "risk_level": "medium"
      }
    ],
    "escalation_mentioned": false,
    "opposition_messages": [
      {
        "user": "経営企画B",
        "text": "でも、まだやめられないですよね？",
        "type": "opposition"
      }
    ],
    "has_concern": true
  }
}
```

**確認ポイント:**
- ✅ `parsed.risk_messages` にリスクメッセージが含まれている
- ✅ `parsed.opposition_messages` に反対意見が含まれている
- ✅ `parsed.has_concern` が `true`

### Google Workspaceサービス（リサーチ・分析・資料作成）

**エンドポイント:** `POST /api/execute` を実行すると、内部的にGoogle Workspaceサービスが呼び出されます。

**確認方法:**
1. 実行を開始: `POST /api/execute`
2. 実行状態を確認: `GET /api/execution/{execution_id}`
3. 実行結果を確認: `GET /api/execution/{execution_id}/results`

**期待されるレスポンス（実行結果）:**
```json
{
  "execution_id": "...",
  "results": [
    {
      "type": "document",
      "name": "3案比較資料の自動生成",
      "download_url": "https://drive.google.com/file/d/mock_file_id/view"
    },
    {
      "type": "research",
      "name": "市場データ分析",
      "data": {
        "topic": "ARPU動向",
        "results": [...]
      }
    }
  ]
}
```

**確認ポイント:**
- ✅ `results` にリサーチ、分析、資料作成の結果が含まれている
- ✅ `download_url` が生成されている

### Google Driveサービス（結果保存・ダウンロード）

**エンドポイント:** `GET /api/download/{file_id}`

**リクエスト例:**
```bash
curl http://localhost:8000/api/download/mock_file_id
```

**期待されるレスポンス:**
```json
{
  "file_id": "mock_file_id",
  "download_url": "https://drive.google.com/file/d/mock_file_id/view",
  "filename": "3案比較資料.pdf"
}
```

**確認ポイント:**
- ✅ `download_url` が返される
- ✅ `filename` が設定されている

## 2. Swagger UIで確認

ブラウザで以下のURLを開いて、インタラクティブにAPIをテストできます：

http://localhost:8000/docs

各エンドポイントをクリックして「Try it out」ボタンを押すと、実際にAPIを呼び出してレスポンスを確認できます。

## 3. フロントエンドから確認

フロントエンドのデモページ（http://localhost:3000/demo/case1）で、以下のフローを実行すると、各サービスが呼び出されます：

1. **「Helmがある場合を見る」** → Google Meet/Chatサービスが呼び出される
2. **「Helm解析結果を見る」** → 構造的問題検知が実行される
3. **「AI実行を開始」** → Google Workspace/Driveサービスが呼び出される

ブラウザの開発者ツール（F12）の「Network」タブで、APIリクエストとレスポンスを確認できます。

## 4. ログで確認

バックエンドのコンソールに、各サービスの呼び出しログが表示されます。

**例:**
```
INFO:     POST /api/meetings/ingest
INFO:     Google Meet Service: Processing meeting meeting_001
INFO:     POST /api/chat/ingest
INFO:     Google Chat Service: Processing chat chat_001
```

## 5. モックデータの実装を確認

各サービスの実装ファイルを確認することで、モックデータがどのように生成されているかを確認できます：

- `Dev/backend/services/google_meet.py` - Google Meetモック実装
- `Dev/backend/services/google_chat.py` - Google Chatモック実装
- `Dev/backend/services/google_workspace.py` - Google Workspaceモック実装
- `Dev/backend/services/google_drive.py` - Google Driveモック実装

## 6. 実際のGoogleサービスとの違い

現在のモック実装では：

- ✅ **データ構造は実際のAPIと同じ** - 実際のGoogleサービスに置き換えても、同じデータ構造を返す
- ✅ **ビジネスロジックは実装済み** - パース処理、データ抽出などのロジックは実装されている
- ⚠️ **実際のAPI呼び出しは未実装** - 実際のGoogle APIへの接続はまだ実装されていない

## 7. 実際のGoogleサービス統合への移行

実際のGoogleサービスを使用するには：

1. Google Cloud Projectの設定
2. 認証情報の設定（サービスアカウントまたはOAuth2）
3. 各サービスのモック関数を実際のAPI呼び出しに置き換え

詳細は [SETUP.md](./SETUP.md) を参照してください。

## 確認チェックリスト

- [ ] Google Meetサービス: 議事録が正しくパースされている
- [ ] Google Chatサービス: チャットメッセージが正しくパースされている
- [ ] Google Workspaceサービス: リサーチ・分析・資料作成の結果が返される
- [ ] Google Driveサービス: ダウンロードURLが生成される
- [ ] フロントエンドでデモが正常に動作する
- [ ] APIドキュメント（Swagger UI）で各エンドポイントが動作する

