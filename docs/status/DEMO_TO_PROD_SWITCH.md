# DEMO → PROD 切り替えガイド（モックと本番実装の境界）

最終更新: 2026-01-21

## 1. 全体ポリシー

- 事前ハッカソンでは **「モックだが現実的」な挙動** を優先しつつ、
  - サービス層インターフェース
  - API エンドポイント
  - 型・レスポンス構造
  は **本番を前提に固定** する。
- デモ専用の演出は、できる限り
  - フロントエンド側の表示ロジック
  - モックデータの中身
  に閉じ込め、IFを汚さない。

## 2. モード切り替えの仕組み

### 環境変数・設定フラグ（例）

- 共通
  - `USE_LLM=true/false`  
  - `LLM_MODEL=models/gemini-1.5-flash` (gemini-2.0-flash-001は廃止予定のため更新)
- Google API 関連
  - `GOOGLE_APPLICATION_CREDENTIALS`（サービスアカウント）
  - `GOOGLE_OAUTH_CREDENTIALS_FILE`（OAuth）
  - `GOOGLE_DRIVE_FOLDER_ID`（保存先フォルダ）
- デモ/本番モード
  - `USE_REAL_GOOGLE_API=true/false`
  - `USE_DEMO_DATA=true/false`

### バックエンドでの判定イメージ

- `GoogleMeetService`, `GoogleChatService`, `GoogleWorkspaceService` などで、
  - 認証情報ファイルの有無
  - 上記フラグ
  をもとに `self.use_mock` を決定
- 実装パターン
  - `use_mock = not self.use_oauth and not self.use_service_account`
  - 実 API で失敗した場合も、基本はモックにフォールバック

## 3. サービス層インターフェース（守るべき境界）

### Google Meet

- ファイル: `backend/services/google_meet.py`
- 代表メソッド
  - `get_transcript(meeting_id: str) -> Dict[str, Any]`
    - 戻り値はモック/実API共通で
      - `meeting_id`
      - `transcript: str`
      - `metadata: { meeting_name, date, participants, ... }`
    - 実 API 版では Google Meet API v2 から構築、モック版ではサンプル議事録を返す

### Google Chat

- ファイル: `backend/services/google_chat.py`
- 代表メソッド
  - `get_chat_messages(chat_id: str, channel_name: Optional[str]) -> Dict[str, Any]`
    - 戻り値
      - `messages: [{ user, text, timestamp }]`
      - `metadata: { project_id, meeting_id, ... }`
    - 実 API 版では Chat API から取得、モック版ではサンプルチャットを返す

### Google Workspace（リサーチ・分析・資料作成）

- ファイル: `backend/services/google_workspace.py`
- 代表メソッド
  - `research_market_data(topic: str) -> Dict[str, Any>`
  - `analyze_data(data: Dict[str, Any]) -> Dict[str, Any>`
  - `generate_document(content: Dict[str, Any], document_type: str) -> Dict[str, Any>`
  - `send_notification(recipients: List[str], message: str, subject: str) -> Dict[str, Any>`
- 重要ポイント
  - モックでも「将来の実 API でそのまま使える引数・戻り値」にしておく
  - 実装が追いつかない箇所は、`TODO` コメントで「どの API を想定しているか」を明示

## 4. フロントエンド側の切り替えポイント

### API クライアント（`lib/api.ts`）

- エンドポイントと型は **本番想定で固定**
  - `/api/meetings/ingest`
  - `/api/chat/ingest`
  - `/api/analyze`
  - `/api/escalate`
  - `/api/approve`
  - `/api/execute`
  - `/api/execution/{id}`
  - `/api/execution/{id}/results`
- フロントエンドは「モックだから特別なことをする」のではなく、
  - 常に同じ型を受け取り、
  - 実/モックの違いは「中身のリアリティ」のみ、という構造を維持。

### デモ専用ロジックの扱い

- 例: `app/demo/case1/page.tsx` の AI 実行ステップ表示
  - バックエンドの `ExecutionResult.tasks` とは独立した「ストーリー用の表示」だが、
  - 実装側では、将来タスク名や数を合わせられるようにしておく。
- どうしてもデモ専用の分岐が必要な場合:
  - クエリパラメータや環境変数で制御
    - 例: `/demo/case1?demoMode=true`
  - ビジネスロジックには入れず、プレゼン用の UI 挙動に閉じ込める。

## 5. DEMO → PROD 切り替えのステップ例

1. **Meet/Chat の実データを一部接続**
   - `GOOGLE_APPLICATION_CREDENTIALS` または `GOOGLE_OAUTH_CREDENTIALS_FILE` を設定
   - `USE_REAL_GOOGLE_API=true` で一部エンドポイントを実モードに
   - エラー時は自動的にモックへフォールバックすることを確認

2. **Workspace（Docs / Drive）の本番化**
   - `GoogleWorkspaceService.generate_document` で実 Docs API に切り替え
   - `GOOGLE_DRIVE_FOLDER_ID` を PoC 用フォルダに設定
   - モックと同じインターフェースでドキュメント情報を返す

3. **通知まわりの段階的自動化**
   - 初期段階:
     - `send_notification` は「送信ログを残すだけ」 or 「Draft を作るだけ」
   - 次の段階:
     - 実際に Gmail / Chat に送るが、対象は開発チームやテスト用スペースに限定
   - 本番運用:
     - RBAC や承認フローを噛ませた上で自動送信を有効化

## 6. 事前ハッカソンでの伝え方

- 伝えたいポイント
  - 「今日のデモはモック中心だが、**インターフェースとフローは本番を前提に設計済み**」
  - 「後から中身（実 API や実データ）を差し替えるだけで、本番化に持っていける」
- 想定される質問
  - Q: 「このモックから本番にする時、どこを変える必要がありますか？」  
    A: 上記 2〜5 章の内容をベースに、「サービス層の実装切り替え」と「環境変数の設定変更」で完結することを説明。

