## Helm アーキテクチャ設計（1か月後・中間ハッカソン版）

### 0. ゴール定義（現実的な到達ライン）

> 前提: 個人 or 少人数チーム / 中級エンジニアが 1か月で到達できる範囲に抑える

- **最低限「Helm らしく」動くこと（MUST）**
  - 多様な情報源（Slack、会議議事録、スライド、データ分析結果）を取り込み
  - LLMによる構造的問題の解釈と説明テキストを出し
  - Human Executive が Web UI 上で「AIから呼ばれる」体験をできる
  - 人の判断後のAI自律実行フローを実現
- **未来の完成像が想像できること（SHOULD）**
  - 組織グラフの可視化
  - 構造介入案（パッチ）の一覧
  - 実行可能タスクリストの表示
  - 将来は自動適用できそうだと分かるレベルの JSON 構造
- **実装していない部分も、モック or 操作イメージがあること（OPTIONAL）**
  - 情報源パーサーの一部（スライド抽出など）はモックでも可
  - 「将来この情報源がこのように取り込まれる」というダミーデータを用意

---

### 0.1 優先度タグの意味

- **MUST**: 1か月でここまで動いていれば「中間ハッカソンとして十分」
- **SHOULD**: 時間があれば入れる。落としてもコンセプトは伝わる
- **OPTIONAL**: 完全に余裕があるときだけ。ここに手を出して燃えないようにする

---

## 1. 全体アーキテクチャ（中間版のスコープ）

```text
[データ層]
  ├─ Firestore: 組織構造・責任モデル（MUST）
  └─ 情報源ストレージ（モックデータ中心）
      ├─ Slackログ（JSON形式）
      ├─ 会議議事録（テキスト）
      ├─ スライド資料（PDF/画像 → テキスト抽出）
      └─ データ分析結果（CSV/JSON）

[Helm Core Engine (Cloud Run / 1サービス)]  ← 単一リポジトリ / 単一コンテナを前提（MUST）
  ├─ Information Ingestion Layer        （MUST）
  │    ├─ SlackParser
  │    ├─ MeetingMinutesParser
  │    ├─ SlideExtractor（PDF/画像 → テキスト）
  │    └─ DataAnalysisParser（CSV/JSON）
  │
  ├─ LLM Interpretation Engine          （MUST）
  │    ├─ MultiSourceInterpreter（Vertex AI / Gemini）
  │    │    ├─ 情報源タイプ別プロンプト
  │    │    ├─ 構造的問題パターン抽出
  │    │    └─ アラート判断基準適用
  │    └─ StructuredOutputGenerator（JSON形式で出力）
  │
  ├─ Evaluation Pipeline               （MUST - 新規追加）
  │    ├─ EvaluationCriteriaExtractor（テキストから定量評価基準を抽出）
  │    ├─ QuantitativeEvaluator（定量評価基準に基づいてスコアリング）
  │    └─ ExplainableAlertReasonGenerator（説明可能なアラート理由生成）
  │
  ├─ Meta-Evaluation Layer             （MUST - 新規追加）
  │    ├─ StructuralMetaEvaluator（統合判断）
  │    └─ IntegratedFindingsGenerator
  │
  ├─ Responsibility Model Engine       （MUST - 新規追加）
  │    ├─ ResponsibilityMapper（責任所在の特定）
  │    └─ AccountabilityAnalyzer（責任モデル分析）
  │
  ├─ Escalation Decision Engine        （MUST - 強化）
  │    ├─ RoleSelector（呼び出すロールの選択）
  │    ├─ EscalationReasonGenerator（呼び出す理由の生成）
  │    └─ AlertCriteriaEvaluator（既存）
  │
  ├─ Intervention Planner              （SHOULD）
  │    ├─ PatchGenerator（提案テキスト＋簡易JSON）
  │    └─ ExecutionPlanGenerator（実行可能タスクリスト）
  │
  └─ Execution Orchestrator            （MUST）
       ├─ TaskExecutor（AI自律実行タスク）
       └─ ExecutionStatusTracker

[UI層]（既存のフロントエンドモックに合わせる）
  └─ Web UI (Next.js)
       ├─ データ受領画面（情報源タイプ別表示）
       ├─ Helm解析結果画面（LLM解釈結果の可視化）
       ├─ Executive判断画面（承認/修正ボタン）
       ├─ AI実行中画面（実行タスクの進捗表示）
       └─ 結果受領画面（実行結果の確認）
```

---

## 2. コンポーネント別の具体化（1か月版）

### 2.1 Information Ingestion Layer（新規・MUST）

**目的**: 多様な情報源を統一的に取り込む

- **SlackParser（MUST）**
  - 入力: SlackエクスポートJSON or モックJSON
  - 出力: `{ channel, timestamp, user, text, thread_id }[]`
  - API:
    - `POST /ingest/slack`（モックデータ投入用）
    - `GET /ingest/slack/{log_id}`（取得）

- **MeetingMinutesParser（MUST）**
  - 入力: テキスト形式の会議議事録
  - 出力: `{ meeting_date, participants[], agenda_items[], decisions[] }`
  - API:
    - `POST /ingest/meeting`（モックデータ投入用）
    - `GET /ingest/meeting/{meeting_id}`（取得）

- **SlideExtractor（SHOULD）**
  - 入力: PDF or 画像ファイル
  - 処理: Google Cloud Vision API or PDF解析ライブラリでテキスト抽出
  - 出力: `{ slide_number, title, content, bullet_points[] }`
  - API:
    - `POST /ingest/slides`（モックデータ投入用）
    - `GET /ingest/slides/{slide_id}`（取得）
  - 注意: 1か月版ではモックデータ（既にテキスト化済み）でも可

- **DataAnalysisParser（MUST）**
  - 入力: CSV or JSON形式のKPIレポート
  - 出力: `{ metric_name, value, target, trend, timestamp }[]`
  - API:
    - `POST /ingest/analysis`（モックデータ投入用）
    - `GET /ingest/analysis/{result_id}`（取得）

---

### 2.2 LLM Interpretation Engine（強化・MUST）

**目的**: 多様な情報源から構造的問題を抽出

- **MultiSourceInterpreter（MUST）**
  - Vertex AI / Gemini を使用
  - **情報源タイプ別プロンプト設計**（2段階評価パイプライン）:
    
    **ステップ1: 評価基準の抽出（Evaluation Criteria Extraction）**
    
    **Slackチャット用プロンプト例（評価基準抽出）**:
    ```
    以下のSlackチャットログを分析し、組織構造上の問題を評価するための定量評価基準を定義してください。
    
    テキストから以下の観点で定量評価基準を抽出してください:
    1. 報告遅延の兆候
       - 評価項目: リスク認識から報告までの時間、報告の曖昧さの度合い
       - 定量指標: リスクキーワード出現から報告までの時間（時間）、曖昧表現の出現回数（回）
    2. エスカレーション基準の不明確さ
       - 評価項目: エスカレーション基準の明確性、判断の困難さ
       - 定量指標: エスカレーション基準が言及された回数（回）、判断に迷う表現の出現回数（回）
    3. 意思決定の先送り
       - 評価項目: 決定の先送り回数、決定期限の不明確さ
       - 定量指標: 「次回検討」「後で決める」などの表現の出現回数（回）
    4. リスク認識と報告のギャップ
       - 評価項目: リスク認識の強さと報告の弱さの差
       - 定量指標: リスクキーワードの出現回数（回）、報告の弱さを示す表現の出現回数（回）
    
    出力形式（JSON）:
    {
      "evaluation_criteria": [
        {
          "criterion_id": "criterion_1",
          "criterion_name": "報告遅延の兆候",
          "evaluation_items": [
            {
              "item_name": "リスク認識から報告までの時間",
              "quantitative_metric": "リスクキーワード出現から報告までの時間（時間）",
              "thresholds": {
                "low": 0,
                "medium": 2,
                "high": 6
              },
              "unit": "hours"
            },
            {
              "item_name": "報告の曖昧さの度合い",
              "quantitative_metric": "曖昧表現の出現回数",
              "thresholds": {
                "low": 0,
                "medium": 2,
                "high": 4
              },
              "unit": "count"
            }
          ]
        }
      ]
    }
    ```
    
    **ステップ2: 定量評価と構造的問題の抽出（Quantitative Evaluation & Issue Extraction）**
    
    **Slackチャット用プロンプト例（定量評価）**:
    ```
    以下のSlackチャットログと評価基準を使用して、定量評価を実施し、構造的問題を抽出してください。
    
    テキスト: {slack_chat_log}
    評価基準: {evaluation_criteria}
    
    各評価項目について:
    1. テキストから定量指標を抽出・計算
    2. 評価基準の閾値と比較してスコアを算出（0-100点）
    3. スコアに基づいてseverityを決定（HIGH: 70-100, MEDIUM: 40-69, LOW: 0-39）
    4. 構造的問題があれば抽出
    
    出力形式（JSON）:
    {
      "quantitative_evaluation": [
        {
          "criterion_id": "criterion_1",
          "criterion_name": "報告遅延の兆候",
          "evaluation_items": [
            {
              "item_name": "リスク認識から報告までの時間",
              "extracted_value": 8,
              "unit": "hours",
              "score": 85,
              "threshold_comparison": {
                "low": 0,
                "medium": 2,
                "high": 6,
                "actual": 8,
                "exceeds_high": true
              }
            },
            {
              "item_name": "報告の曖昧さの度合い",
              "extracted_value": 3,
              "unit": "count",
              "score": 65,
              "threshold_comparison": {
                "low": 0,
                "medium": 2,
                "high": 4,
                "actual": 3,
                "exceeds_high": false
              }
            }
          ],
          "overall_score": 75,
          "severity": "HIGH"
        }
      ],
      "structural_issues": [
        {
          "pattern_id": "ES1_報告遅延",
          "severity": "HIGH",
          "quantitative_scores": {
            "criterion_1": 75,
            "criterion_2": 60
          },
          "evidence": "具体的な発言や文脈",
          "affected_roles": ["role1", "role2"],
          "evaluation_explanation": "リスク認識から報告まで8時間かかっており、閾値6時間を超過。曖昧表現も3回出現し、報告の明確性に課題あり。"
        }
      ],
      "alert_triggered": true,
      "alert_reasoning": "報告遅延の兆候スコアが75点（HIGH）で、閾値を超過しているためアラートを発火。"
    }
    ```
    
    **会議議事録用プロンプト例（評価基準抽出）**:
    ```
    以下の経営会議議事録を分析し、組織構造上の問題を評価するための定量評価基準を定義してください。
    
    テキストから以下の観点で定量評価基準を抽出してください:
    1. 正当化フェーズ（KPI悪化認識があるが戦略変更議論がない）
       - 評価項目: KPI悪化の認識度、戦略変更議論の有無
       - 定量指標: KPI悪化の言及回数（回）、戦略変更議論の言及回数（回）
    2. 判断集中（特定人物への意思決定集中）
       - 評価項目: 意思決定者の集中度、反対意見の無視度
       - 定量指標: 同一人物による決定の割合（%）、反対意見の無視回数（回）
    3. 撤退選択肢の排除
       - 評価項目: 撤退選択肢の議論の有無、撤退基準の明確性
       - 定量指標: 撤退選択肢の言及回数（回）、撤退基準の言及回数（回）
    4. 意思決定の先送り
       - 評価項目: 決定の先送り回数、決定期限の不明確さ
       - 定量指標: 「次回検討」「後で決める」などの表現の出現回数（回）
    
    出力形式（JSON）: [評価基準抽出と同様の形式]
    ```
    
    **会議議事録用プロンプト例（定量評価）**:
    ```
    以下の経営会議議事録と評価基準を使用して、定量評価を実施し、構造的問題を抽出してください。
    
    テキスト: {meeting_minutes}
    評価基準: {evaluation_criteria}
    
    各評価項目について定量評価を実施し、スコアに基づいてseverityを決定してください。
    
    出力形式（JSON）: [定量評価と同様の形式]
    ```
    
    **スライド資料用プロンプト例（評価基準抽出）**:
    ```
    以下のスライド資料を分析し、組織構造上の問題を評価するための定量評価基準を定義してください。
    
    テキストから以下の観点で定量評価基準を抽出してください:
    1. 目標値の下方修正の繰り返し
       - 評価項目: 下方修正の回数、修正幅
       - 定量指標: 下方修正の回数（回）、修正幅の平均（%）
    2. リスク要因の軽視
       - 評価項目: リスク要因の言及度、対策の具体性
       - 定量指標: リスク要因の言及回数（回）、対策の具体性スコア（0-100）
    3. 意思決定権限の不明確さ
       - 評価項目: 決定権限の明確性、責任者の特定度
       - 定量指標: 決定権限の言及回数（回）、責任者の特定度（0-100）
    4. 改善アクションの不在
       - 評価項目: 改善アクションの具体性、実行可能性
       - 定量指標: 改善アクションの言及回数（回）、実行可能性スコア（0-100）
    
    出力形式（JSON）: [評価基準抽出と同様の形式]
    ```
    
    **データ分析結果用プロンプト例（評価基準抽出）**:
    ```
    以下のKPIデータを分析し、構造的問題を評価するための定量評価基準を定義してください。
    
    データから以下の観点で定量評価基準を抽出してください:
    1. KPIの連続的な下方修正
       - 評価項目: 下方修正の回数、修正幅
       - 定量指標: 連続下方修正の回数（回）、修正幅の平均（%）
    2. 目標と実績の乖離が拡大
       - 評価項目: 乖離の拡大度、改善傾向
       - 定量指標: 乖離の拡大率（%）、改善傾向スコア（0-100）
    3. 改善アクションの不在
       - 評価項目: 改善アクションの有無、実行可能性
       - 定量指標: 改善アクションの言及回数（回）、実行可能性スコア（0-100）
    4. 撤退基準の不明確さ
       - 評価項目: 撤退基準の明確性、撤退条件の具体性
       - 定量指標: 撤退基準の言及回数（回）、撤退条件の具体性スコア（0-100）
    
    出力形式（JSON）: [評価基準抽出と同様の形式]
    ```

- **StructuredOutputGenerator（MUST）**
  - LLM出力を検証・正規化
  - 出力スキーマ（定量評価を含む）:
    ```json
    {
      "interpretation_id": "uuid",
      "source_type": "slack|meeting|slides|analysis",
      "source_id": "reference",
      "timestamp": "ISO8601",
      "evaluation_criteria": [
        {
          "criterion_id": "criterion_1",
          "criterion_name": "報告遅延の兆候",
          "evaluation_items": [
            {
              "item_name": "リスク認識から報告までの時間",
              "quantitative_metric": "リスクキーワード出現から報告までの時間（時間）",
              "thresholds": {
                "low": 0,
                "medium": 2,
                "high": 6
              },
              "unit": "hours"
            }
          ]
        }
      ],
      "quantitative_evaluation": [
        {
          "criterion_id": "criterion_1",
          "criterion_name": "報告遅延の兆候",
          "evaluation_items": [
            {
              "item_name": "リスク認識から報告までの時間",
              "extracted_value": 8,
              "unit": "hours",
              "score": 85,
              "threshold_comparison": {
                "low": 0,
                "medium": 2,
                "high": 6,
                "actual": 8,
                "exceeds_high": true
              }
            }
          ],
          "overall_score": 75,
          "severity": "HIGH"
        }
      ],
      "findings": [
        {
          "pattern_id": "ES1_報告遅延|B1_正当化フェーズ|...",
          "severity": "HIGH",
          "quantitative_scores": {
            "criterion_1": 75,
            "criterion_2": 60
          },
          "explanation": "Human Executive向けの説明文（3-5行）",
          "evidence": ["証拠1", "証拠2"],
          "affected_roles": ["Executive", "Manager"],
          "evaluation_explanation": "リスク認識から報告まで8時間かかっており、閾値6時間を超過。曖昧表現も3回出現し、報告の明確性に課題あり。"
        }
      ],
      "alert_triggered": true,
      "alert_reasoning": "報告遅延の兆候スコアが75点（HIGH）で、閾値を超過しているためアラートを発火。"
    }
    ```

- **API**:
  - `POST /interpret`（情報源タイプを指定して解釈実行）
    - リクエスト: `{ source_type, source_id }`
    - レスポンス: `{ interpretation_id, status }`
  - `GET /interpretations/{id}`（解釈結果取得）

---

### 2.3 Evaluation Pipeline（新規・MUST）

**目的**: テキストから定量評価基準を抽出し、定量評価に基づいて説明可能なアラート理由を生成

- **EvaluationCriteriaExtractor（MUST）**
  - 入力: `source_text`（情報源テキスト）、`source_type`（情報源タイプ）
  - 処理:
    - LLMを使用して、テキストから定量評価基準を抽出
    - 評価項目、定量指標、閾値を定義
    - 情報源タイプに応じた評価基準を生成
  - 出力: `{ evaluation_criteria[] }`
  - プロンプト: 上記の「評価基準抽出」プロンプトを使用

- **QuantitativeEvaluator（MUST）**
  - 入力: `source_text`（情報源テキスト）、`evaluation_criteria`（評価基準）
  - 処理:
    - LLMを使用して、テキストから定量指標を抽出・計算
    - 評価基準の閾値と比較してスコアを算出（0-100点）
    - スコアに基づいてseverityを決定（HIGH: 70-100, MEDIUM: 40-69, LOW: 0-39）
  - 出力: `{ quantitative_evaluation[], structural_issues[] }`
  - プロンプト: 上記の「定量評価」プロンプトを使用

- **ExplainableAlertReasonGenerator（MUST）**
  - 入力: `quantitative_evaluation`（定量評価結果）、`structural_issues`（構造的問題）
  - 処理:
    - 定量評価結果に基づいて、説明可能なアラート理由を生成
    - スコア、閾値、実際の値、超過状況を明示
    - Human Executiveが納得できる形で説明
  - 出力: `{ alert_reasoning, evaluation_explanation, score_breakdown }`
  - プロンプト例:
    ```
    以下の定量評価結果に基づいて、アラート理由を説明可能な形で生成してください。
    
    定量評価結果: {quantitative_evaluation}
    構造的問題: {structural_issues}
    
    以下の形式で説明してください:
    1. どの評価基準で問題が検出されたか
    2. 実際の値と閾値の比較
    3. スコアの算出根拠
    4. なぜアラートを発火するのか
    
    出力形式:
    {
      "alert_reasoning": "報告遅延の兆候スコアが75点（HIGH）で、閾値を超過しているためアラートを発火。",
      "evaluation_explanation": "リスク認識から報告まで8時間かかっており、閾値6時間を超過。曖昧表現も3回出現し、報告の明確性に課題あり。",
      "score_breakdown": {
        "criterion_1": {
          "criterion_name": "報告遅延の兆候",
          "overall_score": 75,
          "item_scores": [
            {
              "item_name": "リスク認識から報告までの時間",
              "score": 85,
              "extracted_value": 8,
              "threshold": 6,
              "exceeds_threshold": true,
              "explanation": "8時間は閾値6時間を2時間超過しており、報告遅延の兆候が強い"
            }
          ]
        }
      }
    }
    ```

- **評価パイプラインのフロー**:
  1. **評価基準抽出**: テキストから定量評価基準を抽出（LLM）
  2. **定量評価**: 評価基準に基づいて定量スコアを算出（LLM）
  3. **アラート判断**: スコアに基づいてアラートを発火するか判断（ルールベース or LLM）
  4. **説明可能な理由生成**: 定量評価結果に基づいて説明可能なアラート理由を生成（LLM）

- **API**:
  - `POST /evaluate`（評価パイプライン実行）
    - リクエスト: `{ source_type, source_id }`
    - レスポンス: `{ evaluation_id, status }`
  - `GET /evaluations/{id}`（評価結果取得）
    - レスポンス: `{ evaluation_criteria, quantitative_evaluation, alert_reasoning, score_breakdown }`

---

### 2.4 Alert Decision Engine（改善・MUST）

**目的**: 定量評価結果に基づいてアラートを出すか判断し、説明可能な理由を提供

- **AlertCriteriaEvaluator（MUST）**
  - 入力: `quantitative_evaluation`（定量評価結果）、`evaluation_criteria`（評価基準）
  - 処理:
    - 定量評価結果に基づいてアラートを判断
    - ルールベース（シンプルに保つ）:
      - `overall_score >= 70 → alert_triggered = true`（HIGH severity）
      - `overall_score >= 40 AND pattern_id in ["ES1_報告遅延", "B1_正当化フェーズ", "ES2_エスカレーション不明確"] → alert_triggered = true`（MEDIUM severityでも特定パターンはアラート）
      - `exceeds_high_threshold == true → alert_triggered = true`（閾値を超過している場合）
      - その他は `alert_triggered = false`（参考情報として保存）
  - 出力: `{ alert_triggered, alert_reason, score_based_decision }`

- **CombinationPatternEvaluator（SHOULD - 1か月版で基本的な実装）**
  - 目的: 複数メトリクスの組み合わせを最小シグナルとして判定
  - 入力: `metrics`（複数メトリクスの値）、`combination_patterns`（組み合わせパターンの定義）
  - 処理:
    - 基本的な組み合わせパターン（パターン1）を実装:
      - **パターン1: 正当化フェーズの兆候**:
        - 条件: `kpi_downgrade_count >= 2` AND `ignored_opposition_count >= 1` AND `decision_concentration_rate >= 0.7`
        - 説明: KPI下方修正が続き、反対意見が無視され、判断が集中している状態
        - 重み付け: `kpi_downgrade_count` = 0.4, `ignored_opposition_count` = 0.3, `decision_concentration_rate` = 0.3
        - 組み合わせスコア = Σ(メトリクス値 × 重み)
        - 閾値: 組み合わせスコア >= 0.7 → `alert_triggered = true`
    - 3か月版で3つの組み合わせパターンを実装予定
  - 出力: `{ combination_pattern_id, combination_score, alert_triggered, explanation }`

- **SeverityAssigner（MUST）**
  - 入力: `quantitative_evaluation`（定量評価結果）
  - 処理:
    - 定量スコアに基づいてseverityを決定
    - `overall_score >= 70 → severity = "HIGH"`
    - `overall_score >= 40 → severity = "MEDIUM"`
    - `overall_score < 40 → severity = "LOW"`
  - 出力: `{ severity, score_based_severity }`

- **AlertReasonEnhancer（MUST）**
  - 入力: `alert_triggered`（アラート発火フラグ）、`quantitative_evaluation`（定量評価結果）、`score_breakdown`（スコア内訳）
  - 処理:
    - 定量評価結果に基づいて、説明可能なアラート理由を生成
    - スコア、閾値、実際の値、超過状況を明示
    - Human Executiveが納得できる形で説明
  - 出力: `{ alert_reasoning, evaluation_explanation, score_breakdown }`

- **API**:
  - `GET /alerts`（アラート一覧）
    - レスポンス: `[{ alert_id, project_id, pattern_id, severity, overall_score, created_at, interpretation_id }]`
  - `GET /alerts/{id}`（アラート詳細）
    - レスポンス: `{ alert_id, interpretation, findings[], quantitative_evaluation, alert_reasoning, score_breakdown, patch_preview }`

---

### 2.4.1 Time Series Evaluation（時系列評価・SHOULD - 1か月版で基本的な実装）

**目的**: 単発ログではなく、意思決定の時系列パターンを検出

- **TimeSeriesMetricAggregator（SHOULD - 1か月版で基本的な実装）**
  - 目的: 時系列メトリクスを計算
  - 入力: `logs[]`（時間範囲指定されたログ）、`time_window`（時間窓、例：過去4週間）
  - 処理:
    - 基本的な時系列メトリクス（`kpi_downgrade_trend`）を1つ実装:
      - `kpi_downgrade_trend`: KPI下方修正のトレンド（増加/減少/横ばい）
      - 計算方法: 過去4週間の`kpi_downgrade_count`の変化率を計算
      - トレンド判定: 変化率 > 0.2 → 増加、変化率 < -0.2 → 減少、それ以外 → 横ばい
    - 3か月版で3つの時系列メトリクスを実装予定:
      - `decision_delay_trend`: 判断遅延のトレンド（過去4週間の平均リードタイム）
      - `opposition_suppression_trend`: 反対意見無視のトレンド（過去4週間の無視率）
  - 出力: `{ metric_name, trend, change_rate, time_window }`

- **TimeSeriesPatternDetector（3か月版で実装予定）**
  - 目的: 時系列パターンを検出（移動平均、変化点検出、周期性検出）
  - 1か月版では未実装、3か月版で実装予定

- **API**:
  - `GET /metrics/timeseries?project_id={id}&time_window={weeks}`（時系列メトリクス取得）
    - レスポンス: `{ metrics[], time_window, trends[] }`

**注意**: 1か月版では「時間範囲指定によるログ集計」レベル。3か月版で「時系列パターン検出」を実装予定。

---

### 2.5 Meta-Evaluation Layer（新規・MUST）

**目的**: 構造的問題検知を「メタ評価」として位置づけ、複数情報源を統合的に評価

- **StructuralMetaEvaluator（MUST）**
  - 入力: `interpretations[]`（複数情報源からの解釈結果）
  - 処理:
    - 複数の情報源から検出された構造的問題を統合的に評価
    - 「部分的最適解」ではなく「構造全体の統合判断」を生成
    - メタ評価の観点:
      - 複数情報源で一貫して検出される問題
      - 情報源間の矛盾やギャップ
      - 構造全体への影響度
  - 出力: `{ meta_evaluation_id, integrated_findings[], structural_impact, confidence_level }`

- **統合判断のプロンプト例**:
  ```
  以下の複数情報源からの解釈結果を統合的に評価してください。
  
  情報源1（Slack）: {interpretation_1}
  情報源2（会議議事録）: {interpretation_2}
  情報源3（データ分析）: {interpretation_3}
  
  以下の観点で統合判断を行ってください:
  - 複数情報源で一貫して検出される構造的問題
  - 情報源間の矛盾やギャップ
  - 構造全体への影響度
  - 部分的最適解ではなく、構造全体を見た統合判断
  
  出力形式:
  {
    "integrated_findings": [
      {
        "pattern_id": "...",
        "severity": "HIGH|MEDIUM|LOW",
        "evidence_from_sources": ["source1: 証拠1", "source2: 証拠2"],
        "structural_impact": "この問題が構造全体に与える影響",
        "is_partial_optimization": false,
        "requires_structural_change": true
      }
    ],
    "meta_evaluation_summary": "構造全体を見た統合判断の要約"
  }
  ```

- **IntegratedFindingsGenerator（MUST）**
  - 統合判断結果を正規化・検証
  - 出力スキーマ:
    ```json
    {
      "meta_evaluation_id": "uuid",
      "interpretation_ids": ["id1", "id2", "id3"],
      "integrated_findings": [
        {
          "pattern_id": "ES1_報告遅延|B1_正当化フェーズ|...",
          "severity": "HIGH|MEDIUM|LOW",
          "evidence_from_sources": ["source1: 証拠1", "source2: 証拠2"],
          "structural_impact": "構造全体への影響の説明",
          "is_partial_optimization": false,
          "requires_structural_change": true
        }
      ],
      "structural_impact": "統合的な構造への影響",
      "confidence_level": "HIGH|MEDIUM|LOW",
      "meta_evaluation_summary": "構造全体を見た統合判断の要約",
      "timestamp": "ISO8601"
    }
    ```

- **API**:
  - `POST /meta-evaluate`（メタ評価実行）
    - リクエスト: `{ interpretation_ids[] }`
    - レスポンス: `{ meta_evaluation_id, status }`
  - `GET /meta-evaluations/{id}`（メタ評価結果取得）

---

### 2.6 Responsibility Model Engine（新規・MUST）

**目的**: 組織グラフに基づいた責任モデルの活用

- **ResponsibilityMapper（MUST）**
  - 入力: `findings[]`（構造的問題）、`organization_structure`（組織グラフ）
  - 処理:
    - 構造的問題に対して、責任を持つロールを特定
    - 組織グラフのエッジ（decision/approval関係）を参照
    - 責任の所在を明確化
  - 出力: `{ finding_id, responsible_role, accountability_level, escalation_path[] }`

- **AccountabilityAnalyzer（SHOULD）**
  - 構造的問題に対して、誰が責任を持つべきかを分析
  - 現在の責任モデルと理想的な責任モデルのギャップを検出
  - 出力: `{ current_responsibility, ideal_responsibility, gap_analysis }`

- **API**:
  - `GET /responsibility/{finding_id}`（責任所在の取得）
    - レスポンス: `{ responsible_role, accountability_level, escalation_path[] }`

---

### 2.7 Escalation Decision Engine（強化・MUST）

**目的**: AIが「誰を呼ぶべきか」「なぜ呼ぶべきか」を判断

- **RoleSelector（MUST）**
  - 入力: `findings[]`（構造的問題）、`organization_structure`（組織グラフ）、`responsibility_mapping`（責任マッピング）
  - 処理:
    - `affected_roles`と`responsible_role`から、適切なエスカレーション先を決定
    - ルールベース（シンプルに保つ）:
      - `severity == "HIGH" AND affected_roles includes "Executive" → escalate_to = "Executive"`
      - `pattern_id == "ES1_報告遅延" → escalate_to = "Executive"`（報告遅延は経営層の責任）
      - `pattern_id == "B1_正当化フェーズ" → escalate_to = "Executive"`（戦略判断は経営層の責任）
      - `pattern_id == "ES2_エスカレーション不明確" → escalate_to = "Executive"`（エスカレーション基準の設定は経営層の責任）
  - 出力: `{ escalation_target_role, escalation_reason, urgency_level }`

- **EscalationReasonGenerator（MUST）**
  - LLMを使用して、エスカレーション理由を生成
  - プロンプト例:
    ```
    以下の構造的問題を踏まえ、なぜ[Executive]を呼び出すべきかを説明してください。
    
    構造的問題: {findings}
    組織構造: {organization_structure}
    責任マッピング: {responsibility_mapping}
    
    出力形式:
    {
      "escalation_reason": "この問題は[具体的な理由]のため、[Executive]の判断が必要です。",
      "responsibility_clarification": "この問題の責任は[ロール]にありますが、構造的変更には[Executive]の承認が必要です。",
      "why_this_role": "なぜ[Executive]を呼び出すべきかの説明"
    }
    ```

- **API**:
  - `POST /escalate`（エスカレーション判断実行）
    - リクエスト: `{ alert_id, interpretation_id }`
    - レスポンス: `{ escalation_id, target_role, reason, urgency_level }`
  - `GET /escalations/{id}`（エスカレーション詳細取得）

---

### 2.8 Intervention Planner（修正・SHOULD）

- **PatchGenerator（SHOULD）**
  - 入力: `findings[]`（LLM解釈結果）
  - 出力: 介入案（テキスト + 簡易JSON）
  - パッチ例:
    ```json
    {
      "patch_id": "uuid",
      "finding_id": "reference",
      "intervention_type": "structure_change|process_change|role_assignment",
      "description": "Human Executive向けの説明",
      "changes": [
        {
          "target": "組織グラフノード|プロセス|ルール",
          "action": "追加|削除|変更",
          "details": "具体的な変更内容"
        }
      ],
      "expected_impact": "この変更により期待される効果"
    }
    ```

- **ExecutionPlanGenerator（MUST - 新規追加）**
  - 入力: `patch`（介入案）
  - 出力: 実行可能タスクリスト
  - タスク例:
    ```json
    {
      "plan_id": "uuid",
      "patch_id": "reference",
      "tasks": [
        {
          "task_id": "t1",
          "type": "data_collection|analysis|notification|document_generation",
          "description": "市場データ分析",
          "executable_by_ai": true,
          "estimated_duration": "2時間",
          "dependencies": []
        },
        {
          "task_id": "t2",
          "type": "notification",
          "description": "関係部署への通知",
          "executable_by_ai": true,
          "estimated_duration": "30分",
          "dependencies": ["t1"]
        }
      ]
    }
    ```

- **API**:
  - `GET /projects/{id}/plans`（介入案と実行計画）
    - レスポンス: `{ patches[], execution_plans[] }`

---

### 2.9 Execution Orchestrator（新規・MUST）

**目的**: 人の判断後のAI自律実行を管理

- **TaskExecutor（MUST）**
  - 実行可能タスクタイプ:
    1. **データ収集・分析**: 外部API呼び出し、データベースクエリ
    2. **文書生成**: レポート、スライド、メールの自動生成
    3. **通知**: Slack/メール通知の送信
    4. **システム更新**: Firestoreの組織グラフ更新、カレンダー登録
  
  - 実行フロー:
    1. Executive承認後、`ExecutionPlan`を取得
    2. 各タスクを順次実行（依存関係を考慮）
    3. 実行中は進捗をFirestoreに記録
    4. 人の判断が必要な場面では停止して通知

- **ExecutionStatusTracker（MUST）**
  - 実行状態をFirestoreに記録
  - 状態: `pending|running|completed|failed|paused`
  - UIから進捗を取得可能

- **API**:
  - `POST /executions/{plan_id}/start`（実行開始）
    - リクエスト: `{ plan_id }`
    - レスポンス: `{ execution_id, status }`
  - `GET /executions/{id}`（実行状態取得）
    - レスポンス: `{ execution_id, status, progress, current_task, completed_tasks[] }`
  - `GET /executions/{id}/results`（実行結果取得）
    - レスポンス: `{ execution_id, results[], summary }`

---

## 3. データスキーマ（修正版）

### Firestore コレクション

- `organizations/{org_id}/structure`（組織グラフ）
  - `nodes: [{id, type(human/agent), role, name}]`
  - `edges: [{from, to, relation(decision/approval)}]`

- `organizations/{org_id}/sources`（情報源データ）
  - `slack_logs/{log_id}`: `{ channel, timestamp, user, text, thread_id, raw_data }`
  - `meeting_minutes/{meeting_id}`: `{ meeting_date, participants[], agenda_items[], decisions[], raw_text }`
  - `slides/{slide_id}`: `{ slide_number, title, content, bullet_points[], extracted_text }`
  - `analysis_results/{result_id}`: `{ metric_name, value, target, trend, timestamp, raw_data }`

- `organizations/{org_id}/interpretations`（LLM解釈結果）
  - `{ interpretation_id, source_type, source_id, timestamp, findings[], alert_triggered, alert_reasoning }`

- `organizations/{org_id}/evaluation_criteria`（評価基準）
  - `{ criterion_id, source_type, criterion_name, evaluation_items[], thresholds, timestamp }`

- `organizations/{org_id}/quantitative_evaluations`（定量評価結果）
  - `{ evaluation_id, source_id, evaluation_criteria_id, quantitative_evaluation[], overall_score, severity, timestamp }`

- `organizations/{org_id}/score_breakdowns`（スコア内訳）
  - `{ breakdown_id, evaluation_id, criterion_id, item_scores[], overall_score, explanation, timestamp }`

- `organizations/{org_id}/alerts`（アラート）
  - `{ alert_id, interpretation_id, evaluation_id, pattern_id, severity, overall_score, alert_reasoning, evaluation_explanation, score_breakdown, created_at, status(pending|approved|rejected) }`

- `organizations/{org_id}/patches`（介入案）
  - `{ patch_id, finding_id, intervention_type, description, changes[], expected_impact }`

- `organizations/{org_id}/execution_plans`（実行計画）
  - `{ plan_id, patch_id, tasks[], created_at }`

- `organizations/{org_id}/executions`（実行状態・結果）
  - `{ execution_id, plan_id, status, progress, current_task, completed_tasks[], results[], started_at, completed_at }`

- `organizations/{org_id}/meta_evaluations`（メタ評価結果）
  - `{ meta_evaluation_id, interpretation_ids[], integrated_findings[], structural_impact, confidence_level, meta_evaluation_summary, timestamp }`

- `organizations/{org_id}/responsibility_mappings`（責任マッピング）
  - `{ finding_id, responsible_role, accountability_level, escalation_path[], current_responsibility, ideal_responsibility, gap_analysis, timestamp }`

- `organizations/{org_id}/escalations`（エスカレーション記録）
  - `{ escalation_id, alert_id, interpretation_id, target_role, reason, responsibility_clarification, why_this_role, urgency_level, status, created_at }`

---

## 4. UI の具体化（中間版・フロントエンドモックに合わせる）

- 画面A: **データ受領画面**（MUST）
  - 情報源タイプ別にデータを表示
  - Slackログ、会議議事録、スライド、データ分析結果の一覧
  - 各情報源から「Helm解析を開始」ボタン

- 画面B: **Helm解析結果画面**（MUST）
  - LLM解釈結果の可視化
  - パターン、証拠、説明、影響を受けるロールを表示
  - **定量評価結果の可視化**:
    - 評価基準と定量指標の表示
    - スコア（0-100点）とseverityの表示
    - 閾値と実際の値の比較表示
    - スコア内訳の表示
  - アラートが発火した場合は「Executive判断へ」ボタン

- 画面B-2: **メタ評価結果画面**（MUST - 新規追加）
  - 複数情報源からの統合判断結果を表示
  - 「部分的最適解ではなく、構造全体を見た統合判断」であることを明示
  - 情報源間の一貫性・矛盾を可視化
  - 構造全体への影響度を表示

- 画面C-2: **エスカレーション理由画面**（MUST - 新規追加）
  - 「なぜこの人を呼び出すべきか」の説明を表示
  - 責任モデルに基づいたエスカレーション理由
  - 組織グラフでの責任の所在を可視化
  - 「AIが人を呼び出す」仕組みの説明

- 画面C: **Executive判断画面**（MUST）
  - 介入案と実行計画を表示
  - **定量評価結果とアラート理由の表示**:
    - 評価基準と定量指標の表示
    - スコア（0-100点）とseverityの表示
    - 閾値と実際の値の比較表示
    - 「なぜアラートが発火したか」の説明可能な理由
    - スコア内訳の表示
  - エスカレーション理由と責任の所在を表示
  - 「承認する / 一部修正して実行 / 保留する」ボタン
  - 承認後は「AI実行を開始」ボタン

- 画面D: **AI実行中画面**（MUST）
  - 実行タスクの進捗をリアルタイム表示
  - 各タスクの完了状況、依存関係の可視化
  - 実行完了後は「結果を確認」ボタン

- 画面E: **結果受領画面**（MUST）
  - 実行結果を確認
  - 次のPDCAサイクルへの遷移

- 画面F: **組織グラフ表示**（SHOULD／最悪シンプルなリストでも可）
  - ノード: 人 / AI / Helm
  - エッジ: 決裁フローのみ（太線: Executive）

---

## 5. GCP 利用範囲（中間版）

- **Cloud Run**
  - Helm Core Engine（単一サービス） ← **ここだけは必ず触る**
- **Vertex AI / Gemini**
  - MultiSourceInterpreter で **情報源タイプ別プロンプト**を使用（MUST）
- **Firestore**
  - 組織構造 + 情報源データ + 解釈結果 + アラート + 介入案 + 実行状態（MUST）
- **Cloud Vision API（SHOULD）**
  - SlideExtractor でスライド画像からテキスト抽出
  - 1か月版ではモックデータ（既にテキスト化済み）でも可

---

## 6. この段階で「見せられること」

- **テキストから定量評価基準を抽出し、定量評価に基づいて説明可能なアラート理由を生成**
  - 評価パイプラインにより、テキストから定量評価基準を自動抽出
  - 定量スコア（0-100点）に基づいてseverityを決定
  - アラート理由は定量スコアと閾値の比較に基づいて説明可能な形で生成
  - Human Executiveが「なぜアラートが発火したか」を納得できる説明

- **多様な情報源から構造的問題を抽出するLLMの能力**
  - Slack、会議議事録、スライド、データ分析結果の4種類から構造的問題を検出
  - 各情報源タイプに応じた定量評価基準を自動抽出

- **情報源タイプごとの解釈プロセスの違い**
  - 各情報源に最適化された評価基準抽出プロンプトと定量評価プロンプト
  - 情報源タイプごとの評価項目と定量指標の違い

- **人の判断後のAI自律実行フローの具体性**
  - データ収集、分析、文書生成、通知、システム更新を自律実行

- **3か月版で「何を拡張するか」が明確な土台**
  - 情報源の追加、実行タスクの拡張、組織グラフの自動更新など
  - 評価基準の学習と改善（過去の評価結果から評価基準を改善）

---

## 6.1 Helmの差別化ポイント（1か月版で実現・説明できること）

### 6.1.1 他のAIエージェントとの違い

**他のAIエージェント**:
- 完全自動が強みだが、判断や責任はヒトで結局便利ツール止まり
- 上司や他部署のようなメタ評価がAIにできない
- 部分的な最適解をそれぞれ出すため判断に困る
- 人がAIを呼び出して使う（従来型）

**Helm**:
- **AIが必要に応じて必要な人を呼び出す仕組み**（逆転の発想）
- **構造全体を見たメタ評価をAIが行う**（タスクレベルではなく組織構造レベル）
- **複数情報源を統合的に評価し、統合判断を提供**（部分的最適解ではない）
- **責任モデルに基づいたエスカレーション判断**（組織グラフを活用）

### 6.1.2 「AIが人を呼び出す」仕組み

- **自動エスカレーション判断**:
  - Helmは構造的問題を検知すると、自動的に適切なロール（Executive等）を呼び出す
  - 呼び出すロールは、組織グラフと構造的問題の性質から動的に決定される
  - RoleSelectorが`affected_roles`と`responsible_role`を参照して判断

- **エスカレーション理由の生成**:
  - EscalationReasonGeneratorがLLMを使用して、「なぜこの人を呼び出すべきか」を説明
  - 責任モデルに基づいた理由を生成
  - 「この問題の責任は[ロール]にありますが、構造的変更には[Executive]の承認が必要です」といった説明

- **従来型との違い**:
  - 従来型: 人がAIを呼び出して使う（「AIにタスクを依頼する」）
  - Helm: AIが人を呼び出す（「AIが必要に応じて必要な人を呼び出す」）
  - これは「人がAIを呼び出す」従来型とは逆のアプローチ

### 6.1.3 メタ評価としての位置づけ

- **構造的問題検知 = メタ評価**:
  - Helmの構造的問題検知は、「タスクレベルの評価」ではなく「組織構造レベルのメタ評価」
  - これは「上司や他部署のようなメタ評価」をAIが行う仕組み
  - Meta-Evaluation Layerが複数情報源を統合的に評価

- **統合判断の提供**:
  - 複数情報源（Slack、会議議事録、スライド、データ分析）を統合的に評価
  - 情報源間の矛盾やギャップを検出
  - 構造全体への影響を評価
  - 「部分的最適解ではなく、構造全体を見た統合判断」を提供

- **メタ評価の観点**:
  - 複数情報源で一貫して検出される問題
  - 情報源間の矛盾やギャップ
  - 構造全体への影響度
  - 部分的最適解の排除

### 6.1.4 責任モデルの明確化

- **組織グラフに基づいた責任モデル**:
  - Helmは組織グラフに基づいた責任モデルを保持
  - Responsibility Model Engineが構造的問題に対して、誰が責任を持つべきかを明確化
  - 組織グラフのエッジ（decision/approval関係）を参照

- **エスカレーション判断への活用**:
  - エスカレーション判断は、責任モデルに基づいて行われる
  - ResponsibilityMapperが責任の所在を特定
  - Escalation Decision Engineが責任モデルを参照して、適切なロールを選択

### 6.1.5 1か月版での実現範囲

- **実現できること**:
  - AIが構造的問題を検知し、自動的にExecutiveを呼び出す流れ
  - 複数情報源からの統合判断（メタ評価）の可視化
  - エスカレーション理由の説明（「なぜこの人を呼び出すべきか」）
  - 責任モデルに基づいたエスカレーション判断の説明

- **説明できること**:
  - 「他のAIエージェントは部分的最適解を出すが、Helmは構造全体を見た統合判断を提供する」
  - 「他のAIエージェントは人がAIを呼び出すが、HelmはAIが人を呼び出す」
  - 「Helmはタスクレベルの評価ではなく、組織構造レベルのメタ評価を行う」
  - 「Helmは責任モデルに基づいて、適切なロールを自動的に呼び出す」

---

## 7. 実装上のクリティカルポイントと注意点（1か月版）

- **① 評価パイプラインが最重要**
  - テキストから定量評価基準を抽出し、定量評価に基づいて説明可能なアラート理由を生成
  - 評価基準の抽出プロンプトと定量評価プロンプトの品質が結果を左右する
  - アラート理由は定量スコアと閾値の比較に基づいて説明可能な形で生成
  - ルールエンジンより評価パイプラインの品質を優先

- **② 情報源パーサーは段階的実装**
  - 最初はSlack + 会議議事録の2種類から開始（MUST）
  - スライド・データ分析はSHOULD（モックデータでも可）
  - 後から追加可能な設計にする

- **③ アラート判断は定量評価に基づく**
  - アラート判断は定量スコアと閾値の比較に基づいて行う
  - スコアに基づいたseverity決定（HIGH: 70-100, MEDIUM: 40-69, LOW: 0-39）
  - アラート理由は定量評価結果に基づいて説明可能な形で生成
  - 複雑なルールエンジンは作らないが、定量評価は必須

- **④ 実行フローは具体化**
  - 「AIが何を実行できるか」を明確に定義（モックでも可）
  - 実行可能タスクタイプを4種類に限定
  - 依存関係の管理をシンプルに保つ

- **⑤ UI は「見た目よりも流れ」を優先**
  - 既存のフロントエンドモックに合わせる
  - 重要なのは、データ受領 → 解析 → 判断 → 実行 → 結果の流れが明確であること

- **⑥ スコープを絶対に増やさない**
  - LIVEモードや音声入力は **3か月版のみ**。1か月版には入れない。
  - 情報源の自動取得（Slack API連携など）は3か月版で実装

- **⑦ メタ評価は1か月版では簡素化**
  - 複数情報源の統合評価は実装するが、完全なメタ評価機能は3か月版で拡張
  - 1か月版では、2-3種類の情報源を統合的に評価する程度でOK

- **⑧ エスカレーション判断はシンプルに**
  - ルールベースで十分。LLMによる判断は3か月版で検討
  - RoleSelectorはシンプルなルール（severity、pattern_id、affected_roles）で判断

- **⑨ 責任モデルは組織グラフを活用**
  - 1か月版では組織グラフの基本構造を参照する程度でOK
  - AccountabilityAnalyzerはSHOULD（時間があれば実装）

- **⑩ 評価パイプラインの実装順序**
  - ステップ1: 評価基準抽出プロンプトの設計とテスト
  - ステップ2: 定量評価プロンプトの設計とテスト
  - ステップ3: 説明可能なアラート理由生成プロンプトの設計とテスト
  - ステップ4: 評価パイプライン全体の統合テスト
  - 各ステップで、実際のデータで評価基準とスコアが妥当か検証

---

## 8. パターンID一覧（参考）

### エスカレーション関連
- `ES1_報告遅延`: リスク認識があるが報告が遅延している
- `ES2_エスカレーション不明確`: エスカレーション基準が不明確

### ビジネスプロジェクト関連
- `B1_正当化フェーズ`: KPI悪化認識があるが戦略変更議論がない
- `B2_撤退選択肢排除`: 撤退選択肢が構造的に排除されている
- `B3_判断集中`: 意思決定が特定人物に集中している

### 機会損失関連
- `O1_機会認識と権限不一致`: 機会は認識されているが決定権限が不在
- `O2_意思決定長期化`: 意思決定プロセスが長期化している

---
