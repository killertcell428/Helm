## Helm アーキテクチャ設計（3か月後・本番大会版）

### 0. ゴール定義（3か月で現実的に到達するライン）

> 前提: 中級エンジニアが 3か月（週末＋平日夜ベース想定）で到達可能な範囲

- **中間版（1か月）の「実際の完成版」（MUST）**
  - Observer / Evaluator / Planner / Orchestrator のループが  
    実データで安定して回る
  - 少なくとも 1つのユースケース（新規事業 or 研究）で  
    「Before/After の構造変化とKPI変化」をデモできる
- **さらにその先のロードマップの実現可能性を示す（SHOULD）**
  - 組織グラフの「実際の再構成」（パッチの自動適用）
  - 2つ目のドメイン（研究 or ビジネス）の **一部実装**
  - 拡張しやすい形での API / スキーマ設計

※ 3つ以上のユースケースや複雑な自律エージェントは「やりすぎ」なので切る。

---

## 1. 全体アーキテクチャ（本番版のスコープと優先度）

```text
[データ層]
  ├─ BigQuery: 成果/判断/介入ログ（実運用レベルのスキーマ）
  ├─ Firestore: 組織構造・責任モデル・ルール・適用履歴
  └─ （任意）Cloud Storage: 生ログ・エクスポート用

[Helm Core Engine (Cloud Run)]         ← ここが3か月の中心開発対象（MUST）
  ├─ Structure Observer               （MUST）
  │    ├─ LogFetcher（複数テーブル対応）
  │    ├─ LogNormalizer（汎用化）
  │    └─ MetricAggregator（指標の追加）
  ├─ Structure Evaluator              （MUST）
  │    ├─ RuleEngine（ルール拡張 + 設定ファイル化）
  │    ├─ PatternLibrary（R1/B1 以外のパターンも追加）
  │    └─ ExplanationGenerator（プロンプト整理）
  ├─ Intervention Planner             （MUST）
  │    ├─ PatchGenerator（Firestore 組織グラフへの実パッチ）
  │    ├─ RiskImpactEstimator（簡易スコアリング → UI表示）
  │    └─ PlanSerializer（外部からも読める形式）
  └─ Escalation Orchestrator          （MUST）
       ├─ EscalationDecider（3段階: auto / exec / board）
       ├─ NotificationAdapter（Web UI + Slack 等に対応可）
       └─ CommitApplier（Firestore 更新 + BigQuery ログ）

[Domain Agents 層]                     ← Bizを「本命」、R&Dは「おまけ」として扱う
  ├─ Biz Agents（新規事業ユースケース：本命）
  │    ├─ KPI Aggregator Agent
  │    └─ Decision Log Structuring Agent
  └─ R&D Agents（研究ユースケース：一部実装 / SHOULD）
       └─ Experiment Log Structuring Agent（単純なもの）  ← ここは時間があれば

[UI層]                                ← 画面数は増やしすぎない（MUST）
  └─ Web UI
       ├─ プロジェクト一覧 + 健全度
       ├─ 組織グラフビュー（差分表示付き）
       ├─ アラート一覧
       ├─ アラート詳細 + 介入案 + 承認フロー
       ├─ Before/After 比較ダッシュボード
       └─ LIVEセッションビュー（当日用：音声/テキスト入力＋即時再評価）
```

---

## 2. Helm Core Engine の完成版イメージ

中間版で作ったコンポーネントをベースに、「本番でここまでは動いている」と言えるラインを定義する。

### 2.1 Structure Observer（本番スコープ・現実的要件）

- **LogFetcher（MUST）**
  - 複数テーブルに対応：
    - `decision_logs`
    - `kpi_logs`
    - `meeting_logs`（議事録由来の構造化テキスト）
  - プロジェクトごとのフィルタリング + 時間範囲指定（MUST）
  - パフォーマンス:
    - PoCでは **数千レコード程度** を想定し、  
      数万レコード以上は無理に最適化しない（SHOULD止まり）

- **LogNormalizer（MUST）**
  - 中間版の `DecisionEvent` / `KpiEvent` に加えて：
    - `MeetingEvent { participants, topics, dissent_flag, timestamp }`
  - 後続の Evaluator / Planner が **ドメイン横断で扱える形** に整形

- **MetricAggregator（MUST）**
  - 指標セットを拡張：
    - `decision_concentration_rate`
    - `kpi_downgrade_count`
    - `ignored_opposition_count`
    - `dissent_suppression_index`（反対意見が議事録レベルで潰されている度合い）
  - 結果を JSON で保存し、再計算なしで UI からも閲覧可能にする。

- **TimeSeriesMetricAggregator（MUST - 3か月版で実装）**
  - 時系列メトリクスを計算：
    - `kpi_downgrade_trend`: KPI下方修正のトレンド（増加/減少/横ばい）
    - `decision_delay_trend`: 判断遅延のトレンド（過去4週間の平均リードタイム）
    - `opposition_suppression_trend`: 反対意見無視のトレンド（過去4週間の無視率）
  - 時系列パターン検出：
    - 移動平均によるトレンド検出
    - 変化点検出（例：KPI下方修正が急増した時点）
    - 周期性検出（例：四半期ごとのKPI下方修正）
  - 結果を JSON で保存し、UI からも閲覧可能にする。

- **TimeSeriesPatternDetector（MUST - 3か月版で実装）**
  - 時系列パターンを検出：
    - 移動平均によるトレンド検出
    - 変化点検出（例：KPI下方修正が急増した時点）
    - 周期性検出（例：四半期ごとのKPI下方修正）
  - 検出されたパターンが構造的問題の兆候かどうかを判定
  - 出力: `{ pattern_id, pattern_type, detected_at, severity, explanation }`

---

### 2.2 Structure Evaluator（本番スコープ・現実的要件）

- **RuleEngine（MUST）**
  - ルールを **外部設定ファイル（YAML/JSON）化**（SHOULD）：
    - 例: `rules/business.yaml`, `rules/research.yaml`
  - 新規ルール追加が「コード変更なしでできる」構造を示す。
  - **組み合わせパターンの定義**（MUST - 3か月版で実装）：
    - パターン1: 正当化フェーズの兆候
      - 条件: `kpi_downgrade_count >= 2` AND `ignored_opposition_count >= 1` AND `decision_concentration_rate >= 0.7`
    - パターン2: エスカレーション遅延の兆候
      - 条件: `ES1_報告遅延` AND `decision_concentration_rate < 0.5` AND `ignored_opposition_count >= 2`
    - パターン3: Zombie Project化の兆候
      - 条件: `kpi_downgrade_count >= 3` AND `B1_justification_phase` AND `decision_concentration_rate >= 0.8`
  - 組み合わせパターンは外部設定ファイルで定義可能にする。

- **PatternLibrary（MUST）**
  - パターン数を 4〜6 まで拡張（SHOULD。最低3つ動けばOK）：
    - 研究: R1_判断先送り, R2_仮説ピボット遅延
    - ビジネス: B1_正当化フェーズ, B2_Zombie Project, B3_責任分散
  - 各パターンごとに：
    - 対応する指標セット
    - 人への説明テンプレ
    - 推奨介入カテゴリ（例: `change_responsibility`, `force_escalation`）

- **ExplanationGenerator (LLM)（MUST）**
  - プロンプトを 2種類に整理：
    1. **短いアラート文**（UIリスト用）
    2. **詳細説明文**（詳細画面用・図解に対応できるレベル）
  - ハッカソン本番までに、実際に“例をいくつか見せられる”状態にする。

---

### 2.3 Intervention Planner（本番スコープ・現実的要件）

- **PatchGenerator（MUST）**
  - 実際に Firestore 組織グラフに適用できるパッチ構造を設計：
    - `Patch { target_node, operation(add/remove/update), payload }`
  - Biz ユースケースについては
    - 「Executive に合議ノードを追加」
    - 「特定 KPI の承認フローを変更」
    など **1〜2パターンは実際に適用して見せる**。

- **RiskImpactEstimator（SHOULD）**
  - 本番では、以下のような数値を実計算：
    - 影響を受けるノード数
    - 新たに増える承認ステップ数
  - UIには「この変更は◯人に影響／承認ステップ+1」のような表示。

- **PlanSerializer（MUST）**
  - 外部からも扱いやすい JSON 形式で保存：
    - `/projects/{id}/plans` で取得可能にし、
    - 将来は API 経由で別システムが読む拡張余地を示す。

---

### 2.4 Escalation Orchestrator（本番スコープ・現実的要件）

- **EscalationDecider（MUST）**
  - 3段階のエスカレーションを実装：
    - `AUTO`: 低リスク → 自動適用（ログだけ残す）
    - `EXEC`: 中〜高リスク → 単一 Executive 承認
    - `BOARD`: 重大案件 → 複数人の承認が必要（将来拡張を示す）

- **NotificationAdapter**
  - MVPでは Web UI 中心だが、本番時点で（SHOULD）：
    - 余裕があれば Slack Webhook かメール送信のどちらか 1つを実装  
    - 時間が厳しければ **Web UI だけでもOK**（NotificationAdapterは抽象設計のみ）

- **CommitApplier（MUST）**
  - Firestore の組織グラフへの実書き込みを実装：
    - パッチ適用前後のスナップショットを BigQuery に保存
    - UI 上で Before/After を比較できるようにする。

---

## 3. Domain Agents 層（本番スコープ）

### 3.1 Biz Agents（新規事業ユースケース：本命・MUST）

- **KPI Aggregator Agent（MUST）**
  - Cloud Run 上の小さなサービスとして実装し、  
    - 事業KPIソース（モック or 既存システム）からデータを集約
    - BigQuery の `kpi_logs` に書き込む

- **Decision Log Structuring Agent（MUST）**
  - 会議メモ（テキスト）を入力として、
    - Vertex AI / Gemini で構造化（誰が何を主張／反対したか）
    - `meeting_logs` と `decision_logs` に書き込む

→ ここまで動けば、「Helm が見るログの一部は**本当にエージェントが作っている**」と示せる。

### 3.2 R&D Agents（研究ユースケース：一部実装・SHOULD）

- **Experiment Log Structuring Agent（SHOULD）**
  - 実験ノート（モックテキスト）から
    - 実験成功/失敗
    - 仮説ID
  を抽出し、BigQuery に書き込む最小限の実装。

→ 研究ユースケースは、「ログが入ってくれば Helm が同じ構造で動く」ことを見せる位置づけ。

---

## 4. UI 層（本番スコープ・画面数と複雑度の制御）

- **画面A: プロジェクト一覧 + 健全度**（MUST）
  - 健全度インジケータを「メータ」や「カラー」で表示
  - クリックで詳細へ遷移

- **画面B: 組織グラフ + Before/After 差分**（MUST）
  - ノード・エッジの Before/After を色分け表示
  - 「この変更は Helm による自律介入の結果です」と明記

- **画面C: アラート & 介入案一覧**（MUST）
  - pattern_id / severity / 状態（未承認・承認済・却下など）

- **画面D: アラート詳細 + 承認フロー**（MUST）
  - Explanation（LLM生成文）
  - パッチ内容（JSON → 人向けに整形）
  - 承認 / 却下ボタン

- **画面E: Before/After KPI ダッシュボード**（SHOULD）
  - 例:  
    - 意思決定リードタイム: 7日 → 48h  
    - 代替案検討率: 20% → 65%  
  - あくまで PoC レベルだが、数値変化を視覚的に見せる。

---

## 5. GCP 利用範囲（本番時点で「ここまでは実装」ライン）

- **Cloud Run**
  - Helm Core Engine
  - Biz Agents（KPI Aggregator / Decision Log Structuring）
- **Vertex AI / Gemini**
  - ExplanationGenerator
  - Decision Log Structuring Agent（会議メモ → 構造化）
- **BigQuery**
  - KPI / 判断 / 介入 / Before-After スナップショット
- **Firestore**
  - 組織グラフ
  - 責任・承認ルール
  - パッチ＆適用履歴
- **（オプション導入）Speech-to-Text API**
  - 本番当日の LIVE セッションで、マイク入力をテキストに変換するために使用
  - 失敗時に備え、同じ入力内容を UI からテキストで打てるバックアップを必ず用意

（余力があればの拡張案として、ADK / Agent Builder を Biz Agent の一部に使う選択肢をキープ）

---

## 6. LIVE デモモード設計（音声入力＋安全なフォールバック）

### 6.1 LIVE モードの目的

- 本番当日に、審査員や登壇者のコメントをその場で取り込み、
  - Helm が即時に構造を再評価し
  - 「次の一手」や「構造介入案」を生成する様子を見せる
- 同時に、音声認識トラブルやネットワーク問題があっても
  - **テキスト入力だけで同等のデモが可能** な構成にしておく

### 6.2 LIVE モードの技術フロー

```text
マイク入力
   │（オプション）Speech-to-Text API
   ▼
発言テキスト（あるいはUIから直接入力）
   │
   ▼
Helm LIVE API
  POST /projects/{id}/live-feedback
   │  payload: { speaker_role, text, timestamp }
   ▼
Helm Core Engine
  ├─ live用の簡易LogNormalizer（FeedbackEvent化）
  ├─ 再評価トリガー（Evaluatorを即時起動）
  └─ Intervention Plannerで「次アクション案」を生成
   │
   ▼
LIVEセッションビュー更新
  - 新しい構造診断
  - 「この場で取るべきアクション」候補表示
```

### 6.3 フォールバック戦略（失敗しても破綻しないために）

- **音声認識が不安定な場合**
  - 司会者 or オペレーターが、発言内容をそのまま LIVE ビュー横のテキストボックスに入力
  - 同じ `/live-feedback` API をテキストベースで叩けるようにしておく

- **Helm の再評価が間に合わない場合**
  - あらかじめ用意した 1〜2パターンの「サンプル発言」とその結果を  
    「リハーサル記録」として事前に保存しておき、最悪それを再生するだけでもストーリーが通るようにしておく

- **完全にオフラインになった場合**
  - スライド上で、「LIVE 時に実際に使った `LIVEセッションビュー` のスクリーンショット」と  
    その時の入力テキスト／出力結果を見せる fallback ストーリーを用意

---

## 7. 実装上のクリティカルポイントと注意点（3か月版）

- **① まず Biz ユースケース 1本を「深く」仕上げる**
  - 研究ユースケースは「追加のデモ」であり、最悪なくてもコンセプトは伝わる。
  - 3か月の前半〜中盤は Biz 用のログ・Evaluator・Planner・UI に集中。
- **② 自動化しすぎない**
  - COMPLETELY 自動な構造変更や、多段の自律エージェントはスコープ外。
  - 「提案＋人の承認＋シンプルな自動適用」までにとどめる。
- **③ 外部連携は 0〜1 個に絞る**
  - Slack or メールどちらか 1つだけ、もしくは今回は見送る。
  - 代わりに Web UI 上の体験を磨く方がコスパが良い。
- **④ LIVE モードは“オプションの皮”として扱う**
  - LIVE そのものは SHOULD。  
    「通常デモ（事前ログベース）」が完成してから、最後の1〜2週間で組み込む。



---

## 6. 本番大会で「語れること」

- Helm は単なるアイデアではなく、
  - **構造観測 → 壊れ方判定 → 介入案生成 → 人を呼ぶ → 構造更新**
    のループが、少なくとも 1ユースケースで実際に動いている。
- ドメインが増えても、
  - BigQuery のログスキーマを追加
  - Firestore の組織グラフに新チームを追加
  - 最小限の Domain Agent を足すだけで拡張できる設計。
- 「この3か月でここまで作れた。残りはこのロードマップで進める」という  
  **中長期ロードマップが現実的に見える** アーキ構成になっている。



