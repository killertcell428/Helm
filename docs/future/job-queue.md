# Job Queue（設計のみ）

## 概要

長時間処理（分析・タスク実行・リテンション削除など）を非同期キューで実行し、API の応答時間を短くする。

## 方針

- **キュー基盤**: Cloud Tasks / SQS / Redis 等のキューにジョブを投入。ワーカーがキューをポールして実行。
- **ジョブ種別**: (1) 分析ジョブ (2) 実行タスク群 (3) 保存期間クリーンアップ (4) 通知送信。
- **API との関係**: ingest / analyze / execute は「ジョブを投入して即 202 Accepted と job_id を返す」方式にし、完了は WebSocket または GET /api/jobs/{job_id} で確認する。
- **冪等性**: ジョブは job_id または (resource_type, resource_id) で重複投入を防ぐ。

## 将来実装時のポイント

- 既存の execute バックグラウンドタスクをキュー駆動に移行。実行結果は executions_db に書き、進捗は WebSocket またはポーリングで配信する。
- リテンション削除は日次で Cloud Scheduler からキューに 1 本投入する形にする。
