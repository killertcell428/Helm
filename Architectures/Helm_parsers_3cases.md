## Helm 3ケース用 簡易パーサー設計（3か月版向け）

### 共通モデル: InputEnvelope

```text
InputEnvelope
  - source_type: "meeting" | "chat" | "news"
  - raw_text: str
  - metadata: dict (会議名/参加者/チャネル/URLなど)
```

- 目的: Case1〜3の生テキスト（議事録・チャット・ニュース）を、Helm Coreが扱える
  - DecisionEvent
  - KpiEvent
  のリストに変換するための最小単位。

---

## Case1: 経営会議（meeting）

### 入力の想定

- `raw_text` には、議事録のサマリ（発言者＋テキスト）が含まれる。
  - 例: 「CFO: 今期の成長率は計画を下回っています」「PM: 目標を少し下げてブランド投資フェーズとしましょう」など。
- `metadata`:
  - `meeting_name`, `participants`, `project_id` など。

### 変換ロジック（ざっくり）

1. KPI関連フレーズの検出
   - 「目標」「KPI」「達成」「未達」「下方修正」などのキーワードを検索。
   - 「目標を下げる/現実的にする/ブランド投資フェーズ」→ `KpiEvent.is_target_downgrade = True`
2. 撤退/ピボット議論の有無
   - 「撤退」「中止」「ピボット」「方向転換」などのキーワードが **1回も出てこない** 場合、
     - 正当化フェーズの兆候として `ignored_opposition_count` に影響。
3. 発言者ロール別 DecisionEvent
   - `metadata.participants` から役割（Executive/PM/Dataなど）を判定し、
   - 「続ける/様子を見る/目標を変える」→ type=`continue` or `kpi_change`
   - 「やめるべき」「ピボットすべき」→ `is_opposition=True`

→ 出力:
- DecisionEvent のリスト（会議中の主要な判断）
- KpiEvent のリスト（下方修正があれば1〜数件）

---

## Case2: 重大ミスのチャット（chat）

### 入力の想定

- `raw_text` には、Slack等のチャットログ（発言者＋テキスト）が含まれる。
  - 「すみません、◯◯の設定を間違えてしまいました」「これリリース止めた方がよくないですか？」など。
- `metadata`:
  - `channel_name`, `project_id`, `severity_tag` など（将来拡張）。

### 変換ロジック（ざっくり）

1. インシデント検知
   - 「ミス」「バグ」「インシデント」「やばい」「止める」などのキーワードを検出。
   - 最初のインシデント報告を `DecisionEvent` として `type="other"` で記録。
2. リスク提起メッセージ
   - 「上に上げた方がいい」「PMに相談」「経営に報告」などの文が **あってもスレが途切れている** 場合、
     - `is_opposition=True` として `ignored_opposition_count` に寄与。
3. エスカレーション完了の有無
   - 「PMにエスカレーション済みです」「◯◯さんに報告しました」などがあれば、
     - 後続Runでは `ignored_opposition_count` を0に近づけるイベントに変換。

→ 出力:
- DecisionEvent のリスト（現場でのリスク提起・対応方針）
- KPIへの直接影響は次Run以降で現れることが多いため、このケースではKpiEventは最小限。

---

## Case3: 外部トレンドチャンスニュース（news）

### 入力の想定

- `raw_text` には、ニュース記事の要約や引用文が含まれる。
  - 「今後6ヶ月で◯◯市場が急成長する見込み」「この分野に投資する企業が優位に立つ」など。
- `metadata`:
  - `source_url`, `impact_level`（人手で付与してもよい）など。

### 変換ロジック（ざっくり）

1. チャンスの大きさ
   - 「急成長」「数倍」「市場拡大」などから `impact_level` を推定（low/medium/high）。
2. 関連プロジェクトの紐付け
   - `raw_text` 中のキーワードと `project_id` のタグを突き合わせ、
   - 対象プロジェクトを1〜複数特定（このデモでは1つに固定でも良い）。
3. 意思決定者の不在検知
   - `metadata` に「誰がこのニュースを共有したか」だけが入っていて、
   - 「誰が次のアクションを決めるか」が不明な場合、
     - P1_planning_authority_mismatch の候補として扱う。

→ 出力:
- DecisionEvent のリスト（「ニュース共有」「検討を提案」など）
- KpiEvent は基本的に0（チャンス前の状態）

---

## まとめ

- 3ケースとも、「生テキストを完璧に理解する」のではなく、
  - ◯ KPI下方修正
  - ◯ 撤退/ピボット議論の有無
  - ◯ リスク提起が拾われているか
  - ◯ チャンスに対する意思決定権限の有無
  といった**構造的なシグナル**だけを拾うのがポイント。
- 3か月版では、この設計に沿って `parsers.py` を実装し、Helm Core（observer/evaluator）に渡せばよい。


