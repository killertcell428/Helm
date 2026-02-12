# 冪等性（execute）設計

## 目的

同一の承認（approval_id）に対して execute が複数回呼ばれた場合、二重に実行を開始せず、既存の実行結果を返す。

## 方針

- **キー**: `approval_id` を冪等キーとする。1 approval に対して 1 execution まで許可する。
- **挙動**:
  - 初回: 新規 execution を作成し、バックグラウンドでタスク実行を開始。返却: 新規 execution の ID とステータス。
  - 同一 approval_id で再リクエスト: 既存の execution を検索し、その execution の現在状態を返す。新規タスクは開始しない。

## 実装

- `executions_db` の各レコードに `approval_id` が含まれているため、execute 受付時に「当該 approval_id ですでに execution が存在するか」を検索する。
- 存在する場合: その execution を返し、HTTP 200 で既存リソースとして返す（重複実行ではないことを示すため、レスポンスに `idempotent_replay: true` などを含めてもよい）。
- 存在しない場合: 従来どおり新規 execution を作成し、バックグラウンド実行を開始。

## オプション拡張

- クライアントが `Idempotency-Key` ヘッダで任意キーを送り、キー単位で冪等にする方式にも拡張可能。本フェーズでは approval_id ベースのみとする。
