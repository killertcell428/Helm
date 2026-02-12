# Ownership Model（設計のみ）

## 概要

データとプロセスに対する「所有者」を定義し、アクセス・変更・削除の責任範囲を明確にする。

## 方針

- **リソース単位の owner**: 会議・チャット・分析・エスカレーション・承認・実行それぞれに `owner_id`（ユーザーまたはチームID）を付与する。
- **継承**: 会議を ingest した主体を meeting の owner とし、そこから生成された analysis / escalation / approval / execution は同じ owner を継承するか、承認者で上書き可能とする。
- **アクセス制御**: 参照・承認・実行は owner または admin ロールに限定する（API Key のロールと組み合わせ）。
- **監査**: 所有者変更は監査ログに記録する。

## 将来実装時のポイント

- Firestore / DB のスキーマに `owner_id`, `owner_type` を追加。
- 既存の監査ログ・認証と統合し、リソース取得時に owner チェックを行う。
