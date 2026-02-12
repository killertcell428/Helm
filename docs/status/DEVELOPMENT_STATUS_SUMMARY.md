# 開発状況サマリー

**最終更新**: 2025年2月11日

---

## 現状の開発状況

### コア機能

| 領域 | 内容 |
|------|------|
| **データ取り込み** | Google Meet / Chat / 会議資料の ingest API。パース・構造化まで一通り対応。 |
| **検知・評価** | ルールベース（StructureAnalyzer）＋マルチ視点LLM（4ロール）＋アンサンブルスコアリング。パターン検出でアラート生成。 |
| **アラート・承認** | EscalationEngine（閾値・重要度）、`POST /api/escalate`・`POST /api/approve`。組織グラフ・RACI・承認フローは JSON 定義で制御（後述）。 |
| **AI自律実行** | ADK ベースのマルチエージェント（Research / Analysis / Notification / Document）。WebSocket で進捗配信。Phase1 はモック＋フォールバック完了。 |

### ガバナンス・運用まわり

| 項目 | 仕組み |
|------|--------|
| **認証** | API Key ＋ ロール（`X-API-Key`）。環境変数 `API_KEYS` で有効化。 |
| **監査** | アクション記録と `GET /api/audit/logs` で取得。 |
| **誤検知・精度** | `POST /api/feedback/false-positive` で登録、`GET /api/metrics/accuracy` で指標取得。 |
| **取得範囲・サプレッション** | ホワイトリスト（会議/チャットID）とサプレッション条件（パターン＋リソース）で制御。 |
| **データ保存期間** | 保持日数設定と `POST /api/admin/retention/cleanup` で定期削除。設計は [data-retention.md](../data-retention.md)。 |
| **冪等性** | 同一 approval_id に対する execute の二重実行を防ぐ。設計は [idempotency-execute.md](../idempotency-execute.md)。 |

### 定義ドキュメント（組織グラフ・RACI・承認フロー）

- `backend/config/definitions/` に org_graph・raci・approval_flows を JSON で配置。
- DefinitionLoader / ResponsibilityResolver / ApprovalFlowEngine が EscalationEngine と approve に組み込み済み。
- 多段階承認（例：CFO承認→経営層承認）まで対応。定義が無い場合は経営層・1回承認でフォールバック。
- 永続化は現状ファイルベース。Firestore は設計段階（[docs/future/](../future/) 参照）。

### デプロイ・提出物

| 項目 | 状態 |
|------|------|
| **バックエンド** | Cloud Run デプロイ済み（[API](https://helm-api-dsy6lzllhq-an.a.run.app)）。Gemini 3 Flash 動作確認済み。 |
| **フロントエンド** | Vercel デプロイ済み（[デモ](https://v0-helm-pdca-demo.vercel.app)）。Case1 デモ・WebSocket 進捗・エラーハンドリング対応。 |
| **GitHub** | 公開リポジトリ。 |
| **Zenn記事・デモ動画** | 制作依頼中／進行中。 |

---

## ネクストステップ

### 短期・中期（機能・品質）

- **ADK Phase2**：実 API 統合（Vertex AI Search、Google Drive、Chat/Gmail など）。現在はモック／ドラフト。
- **Case 2 / Case 3**：デモシナリオの実装・拡張。
- **永続化**：検知記録・エスカレーション履歴の DB/Firestore 保存（現状はインメモリ／ファイル）。
- **会議調整・作成**：CalendarAgent などは設計段階。
- **E2E・パフォーマンス**：テスト拡充、レスポンス・負荷の見直し。

### 長期（設計書ベースの拡張）

以下は設計のみ記載。実装時は `docs/future/` を参照。

| テーマ | ドキュメント | 内容 |
|--------|--------------|------|
| オーナーシップモデル | [ownership-model.md](../future/ownership-model.md) | データ・判断のオーナー定義。 |
| マルチテナント | [multi-tenancy.md](../future/multi-tenancy.md) | 事業部・組織ごとのデータ分離とポリシー。 |
| ジョブキュー | [job-queue.md](../future/job-queue.md) | 長時間分析・タスクのキュー・再実行・キャンセル。 |
| 通知ポリシー | [notification-policy.md](../future/notification-policy.md) | ロール別通知・チャネル（メール／Slack 等）。 |

---

## 関連ドキュメント

- [CURRENT_DEVELOPMENT_STATUS.md](./CURRENT_DEVELOPMENT_STATUS.md) - 開発状況の詳細
- [NEXT_STEPS.md](./NEXT_STEPS.md) - 次のステップ（タスク単位）
- [PROJECT_STATUS.md](./PROJECT_STATUS.md) - プロジェクト状況
- [DOCUMENTATION_INDEX.md](../../DOCUMENTATION_INDEX.md) - ドキュメント一覧
