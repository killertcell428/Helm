# データ保存期間と自動削除 設計

## 対象ストア

| ストア | 説明 | 保持日数（推奨） |
|--------|------|------------------|
| meetings_db | 取り込み済み会議データ | 90日 |
| chats_db | 取り込み済みチャットデータ | 90日 |
| materials_db | 会議資料 | 90日 |
| analyses_db | 分析結果 | 180日 |
| escalations_db | エスカレーション | 365日 |
| approvals_db | 承認履歴 | 365日 |
| executions_db | 実行履歴 | 365日 |

## 保持日数の方針

- **会議・チャット・資料**: 分析元データ。分析結果が残る期間よりやや短くし、プライバシーと再分析のバランスを取る。
- **分析・エスカレーション・承認・実行**: 監査・説明責任のため長めに保持。規制要件に応じて延長可能。

## 削除ジョブのトリガー方針

1. **定期実行**: 日次バッチ（例: 深夜）で「作成日時が保持日数を超えたレコード」を削除。
2. **キー**: 各レコードの `created_at` または `ingested_at` を基準とする。存在しない場合は `updated_at` で代替。
3. **順序**: 参照整合性を考慮し、executions → approvals → escalations → analyses → meetings/chats/materials の順で削除するか、外部参照を持たないストアから先に削除。
4. **実装場所**: バックエンドの `services/retention_cleanup.py` のようなモジュールで削除ロジックを実装し、cron または Cloud Scheduler から HTTP エンドポイント（例: `POST /api/admin/retention/cleanup`）を叩く。

## 設定（環境変数）

- `RETENTION_DAYS_MEETINGS`, `RETENTION_DAYS_CHATS`, `RETENTION_DAYS_ANALYSES`, `RETENTION_DAYS_ESCALATIONS` 等でストア別の日数を上書き可能にする。
- 未設定時は上表の推奨値をデフォルトとする。

## 注意

- 現状はインメモリ Dict のため、プロセス再起動でデータは消える。永続化（DB/Firestore）導入後、本設計に基づく削除ジョブを有効化する。
