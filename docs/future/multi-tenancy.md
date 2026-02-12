# Multi-Tenancy（設計のみ）

## 概要

単一インスタンスで複数テナント（組織・部署）のデータを論理分離する。

## 方針

- **テナント識別子**: 各リクエストに `X-Tenant-ID` または API Key にテナントを紐付け、ストアのキーを `tenant_id + resource_id` の複合にする。
- **データ分離**: meetings_db, analyses_db 等を tenant ごとに分離して保持。同一 tenant 内でのみ参照・エスカレーションを許可する。
- **定義のスコープ**: 組織グラフ・RACI・承認フロー定義を tenant 単位で保持（Firestore の `organizations/{org_id}/definitions` など）。
- **管理**: テナント作成・無効化は admin API で行い、課金・利用量は tenant 単位で集計する。

## 将来実装時のポイント

- 現行のインメモリ Dict を `tenant_id` をキーにした二重構造にするか、永続化と同時に tenant カラムを追加する。
- 認証（API Key）に tenant_id を含め、ミドルウェアで request.state.tenant_id を設定する。
