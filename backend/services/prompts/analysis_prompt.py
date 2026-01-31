"""
分析用プロンプト生成
構造的問題検知のためのプロンプトを構築
"""

from typing import Dict, Any, Optional, Tuple


class AnalysisPromptBuilder:
    """分析用プロンプトビルダー"""
    
    @staticmethod
    def build(
        meeting_data: Dict[str, Any],
        chat_data: Optional[Dict[str, Any]] = None,
        materials_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        分析用プロンプトを構築
        
        Args:
            meeting_data: 会議データ（パース済み）
            chat_data: チャットデータ（パース済み、オプション）
            materials_data: 会議資料データ（オプション）
            
        Returns:
            プロンプト文字列
        """
        meeting_transcript, chat_messages, materials_content = AnalysisPromptBuilder._extract_texts(
            meeting_data, chat_data, materials_data
        )
        
        prompt = AnalysisPromptBuilder._build_base_prompt(
            meeting_transcript=meeting_transcript,
            chat_messages=chat_messages,
            materials_content=materials_content,
            role_description="あなたは組織の意思決定プロセスを分析する専門AIです。"
        )
        
        return prompt
    
    @staticmethod
    def build_for_role(
        meeting_data: Dict[str, Any],
        chat_data: Optional[Dict[str, Any]] = None,
        materials_data: Optional[Dict[str, Any]] = None,
        role_id: str = "executive"
    ) -> str:
        """
        特定ロール視点の分析用プロンプトを構築
        
        Args:
            meeting_data: 会議データ（パース済み）
            chat_data: チャットデータ（パース済み、オプション）
            materials_data: 会議資料データ（オプション）
            role_id: 評価ロールID（executive, staff, corp_planning, governance など）
        
        Returns:
            プロンプト文字列
        """
        meeting_transcript, chat_messages, materials_content = AnalysisPromptBuilder._extract_texts(
            meeting_data, chat_data, materials_data
        )
        
        # ロールごとの役割説明（視点と業務内容を明確に定義）
        role_descriptions = {
            "executive": (
                "あなたは上場企業のCEOです。\n"
                "【あなたの視点と業務】\n"
                "- 全社の業績責任とステークホルダー（株主・取締役会）への説明責任を負う\n"
                "- 戦略の妥当性と撤退/投資判断のタイミングを最終決定する\n"
                "- 全社への影響を最優先に考えるため、KPI悪化が続く状況では非常に高い危機感を持つ\n"
                "- 意思決定の遅れや現状維持バイアスは、組織全体の存続リスクとして認識する\n"
                "\n"
                "【評価の特徴】\n"
                "- KPI悪化が継続しているのに戦略変更がない場合、非常に高いリスクスコアを付ける\n"
                "- 撤退判断の遅れは、全社のリソース浪費と機会損失として深刻に捉える\n"
                "- チャットで懸念が示されていても会議で反映されない場合、意思決定プロセスの構造的問題として評価する\n"
                "\n"
                "以下の会議議事録とチャットログを読み、あなたの立場から構造的な意思決定リスクを評価してください。"
            ),
            "staff": (
                "あなたは現場のプロジェクトリーダーです。\n"
                "【あなたの視点と業務】\n"
                "- 日々の実行可能性と現場の負荷・リソース制約を最優先に考える\n"
                "- 実際の作業への直接的な影響（人員削減、予算カット、プロジェクト中止など）がなければ、危機感は相対的に低い\n"
                "- ただし、チャットで現場メンバーから懸念や不安の声が上がっている場合は、それを重視する\n"
                "- 会議での意思決定が現場の実態と乖離している場合に問題を感じる\n"
                "\n"
                "【評価の特徴】\n"
                "- KPI悪化が続いていても、まだ現場への直接的な影響（人員配置変更、予算削減など）がなければ、スコアは中程度\n"
                "- チャットで「このままではまずい」「撤退すべきでは」などの懸念が示されている場合は、それを証拠として評価を上げる\n"
                "- 会議では楽観的な議論が続いているが、チャットでは懸念が示されている場合、情報の非対称性として問題視する\n"
                "- 実行不可能な計画が継続している場合、現場負荷の観点からリスクを評価する\n"
                "\n"
                "以下の会議議事録とチャットログを読み、あなたの立場から構造的な問題や現場にとって危険なパターンを評価してください。"
            ),
            "corp_planning": (
                "あなたは経営企画部長です。\n"
                "【あなたの視点と業務】\n"
                "- KPI管理と事業ポートフォリオ最適化を担当し、データに基づく客観的判断を重視する\n"
                "- 撤退/投資判断のタイミングと、リソース配分の効率性を評価する\n"
                "- 戦略の妥当性を数値データで検証し、感情的な判断を排除する\n"
                "- 事業ポートフォリオ全体のバランスを考慮し、個別事業の感情的な維持を避ける\n"
                "\n"
                "【評価の特徴】\n"
                "- KPI悪化が継続しているのに現状維持の判断が繰り返される場合、非常に高いリスクスコアを付ける\n"
                "- データに基づかない意思決定や、撤退判断の遅れは、戦略上の構造的リスクとして深刻に捉える\n"
                "- 会議で客観的なデータが提示されても、それに基づかない意思決定が行われる場合、意思決定プロセスの問題として評価する\n"
                "- 事業ポートフォリオの観点から、非効率なリソース配分を問題視する\n"
                "\n"
                "以下の会議議事録とチャットログを読み、あなたの立場から戦略上の構造的リスクを評価してください。"
            ),
            "governance": (
                "あなたはガバナンス/リスク管理責任者です。\n"
                "【あなたの視点と業務】\n"
                "- 報告遅延、隠れたリスク、コンプライアンス違反の可能性を監視する\n"
                "- 意思決定プロセスの透明性と、リスク情報の適切な伝達を重視する\n"
                "- 経営層への報告が適切に行われているか、リスクが隠蔽されていないかを評価する\n"
                "- 組織のガバナンス体制の健全性を維持する責任を負う\n"
                "\n"
                "【評価の特徴】\n"
                "- リスクが認識されているにも関わらず、経営層への報告やエスカレーションが遅延している場合、非常に高いリスクスコアを付ける\n"
                "- チャットで懸念が示されているのに、会議では報告されていない場合、報告プロセスの問題として深刻に捉える\n"
                "- 意思決定プロセスの透明性が欠如している場合、ガバナンス上の問題として評価する\n"
                "- 現状維持バイアスが強く、客観的なリスク評価が行われていない場合、リスク管理体制の問題として認識する\n"
                "\n"
                "以下の会議議事録とチャットログを読み、あなたの立場から構造的なリスクとその深刻度を評価してください。"
            ),
        }
        
        role_description = role_descriptions.get(
            role_id,
            "あなたは組織の意思決定プロセスを分析する専門家です。あなた自身の立場から、一貫した基準で評価してください。"
        )
        
        prompt = AnalysisPromptBuilder._build_base_prompt(
            meeting_transcript=meeting_transcript,
            chat_messages=chat_messages,
            materials_content=materials_content,
            role_description=role_description,
            role_id=role_id
        )
        
        return prompt
    
    @staticmethod
    def _extract_texts(
        meeting_data: Dict[str, Any],
        chat_data: Optional[Dict[str, Any]] = None,
        materials_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str, str]:
        """会議・チャット・資料からLLMに渡すテキストを抽出"""
        # 会議議事録のテキストを取得
        meeting_transcript = meeting_data.get("transcript", "")
        if not meeting_transcript and meeting_data.get("statements"):
            statements = meeting_data.get("statements", [])
            meeting_transcript = "\n".join(
                f"{stmt.get('speaker', 'Unknown')}: {stmt.get('text', '')}"
                for stmt in statements
            )
        
        # チャットログのテキストを取得
        chat_messages = ""
        if chat_data:
            messages = chat_data.get("messages", [])
            if messages:
                chat_messages = "\n".join(
                    f"{msg.get('author', msg.get('user', 'Unknown'))}: {msg.get('text', '')}"
                    for msg in messages
                )
        
        # 会議資料のテキストを取得
        materials_content = ""
        if materials_data:
            materials_content = materials_data.get("content", "")
        
        return (
            meeting_transcript or "（議事録なし）",
            chat_messages or "（チャットログなし）",
            materials_content or "（会議資料なし）",
        )
    
    @staticmethod
    def _build_base_prompt(
        *,
        meeting_transcript: str,
        chat_messages: str,
        materials_content: str,
        role_description: str,
        role_id: str = "default",
    ) -> str:
        """共通のプロンプトテンプレートを構築"""
        
        # ロールごとの分析観点を定義
        role_specific_analysis_points = {
            "executive": """【あなたの分析観点（Executiveとして重視すべき点）】

【健全な意思決定が行われている場合（低リスクスコア: 20-40点）】
- 撤退/ピボット議論が適切に行われている → 低リスク（20-30点、LOW/MEDIUM）
- 客観的なデータに基づいた意思決定が行われている → 低リスク（20-30点、LOW/MEDIUM）
- 会議とチャットの内容が一致している（楽観的な会議、楽観的なチャット） → 低リスク（20-30点、LOW/MEDIUM）
- 意思決定プロセスが透明で、多様な意見が反映されている → 低リスク（20-30点、LOW/MEDIUM）
- 戦略変更や撤退判断が適切なタイミングで行われている → 低リスク（20-30点、LOW/MEDIUM）

【構造的問題がある場合（高リスクスコア: 80-100点）】
1. KPI悪化が継続しているのに戦略変更がない場合 → 非常に高いリスクスコア（80-100点、HIGH/HIGH）
2. 撤退判断の遅れは、全社のリソース浪費と機会損失として深刻に捉える → 80-100点、HIGH/HIGH
3. チャットで懸念が示されていても会議で反映されない場合 → 意思決定プロセスの構造的問題（80-100点、HIGH/HIGH）
4. 現状維持バイアスが強く、客観的なリスク評価が行われていない場合 → 組織存続リスク（80-100点、HIGH/HIGH）
5. ステークホルダーへの説明責任を果たせない状況になっていないか → 80-100点、HIGH/HIGH""",
            
            "staff": """【あなたの分析観点（Staffとして重視すべき点）】

【健全な意思決定が行われている場合（低リスクスコア: 20-40点）】
- 撤退/ピボット議論が適切に行われており、現場の実態が反映されている → 低リスク（20-30点、LOW/MEDIUM）
- 会議とチャットの内容が一致している（楽観的な会議、楽観的なチャット） → 低リスク（20-30点、LOW/MEDIUM）
- 実行可能な計画が立てられており、現場の負荷が考慮されている → 低リスク（20-30点、LOW/MEDIUM）
- 現場の意見が会議で適切に反映されている → 低リスク（20-30点、LOW/MEDIUM）

【構造的問題がある場合（高リスクスコア: 50-80点）】
1. 現場への直接的な影響（人員削減、予算カット、プロジェクト中止など）が実際に発生しているか
   → まだ影響がなければ、スコアは中程度（50-70点、MEDIUM/MEDIUM）
2. チャットで現場メンバーから「このままではまずい」「撤退すべきでは」などの懸念が示されているか
   → 懸念があれば、それを証拠として評価を上げる（60-80点、MEDIUM/HIGH）
3. 会議では楽観的な議論が続いているが、チャットでは懸念が示されている場合
   → 情報の非対称性として問題視する（70-80点、HIGH/HIGH）
4. 実行不可能な計画が継続している場合 → 現場負荷の観点からリスクを評価（60-80点、MEDIUM/HIGH）
5. 会議での意思決定が現場の実態と乖離している場合 → 70-80点、HIGH/HIGH""",
            
            "corp_planning": """【あなたの分析観点（Corp Planningとして重視すべき点）】

【健全な意思決定が行われている場合（低リスクスコア: 20-40点）】
- 撤退/ピボット議論が適切に行われており、データに基づいた意思決定が行われている → 低リスク（20-30点、LOW/MEDIUM）
- 客観的なデータに基づいて戦略が再評価され、適切な判断が行われている → 低リスク（20-30点、LOW/MEDIUM）
- 事業ポートフォリオの観点から、リソース配分が最適化されている → 低リスク（20-30点、LOW/MEDIUM）
- 会議で客観的なデータが提示され、それに基づいた意思決定が行われている → 低リスク（20-30点、LOW/MEDIUM）

【構造的問題がある場合（高リスクスコア: 80-100点）】
1. KPI悪化が継続しているのに現状維持の判断が繰り返される場合 → 非常に高いリスクスコア（80-100点、HIGH/HIGH）
2. データに基づかない意思決定や、撤退判断の遅れ → 戦略上の構造的リスクとして深刻に捉える（80-100点、HIGH/HIGH）
3. 会議で客観的なデータが提示されても、それに基づかない意思決定が行われる場合
   → 意思決定プロセスの問題として評価（80-100点、HIGH/HIGH）
4. 事業ポートフォリオの観点から、非効率なリソース配分を問題視する → 80-100点、HIGH/HIGH
5. 感情的な判断がデータに基づく判断を上回っている場合 → 80-100点、HIGH/HIGH""",
            
            "governance": """【あなたの分析観点（Governanceとして重視すべき点）】

【健全な意思決定が行われている場合（低リスクスコア: 20-40点）】
- リスクが適切に経営層へ報告され、エスカレーションが適切に行われている → 低リスク（20-30点、LOW/MEDIUM）
- 会議とチャットの内容が一致しており、リスク情報が適切に伝達されている → 低リスク（20-30点、LOW/MEDIUM）
- 意思決定プロセスが透明で、リスク評価が客観的に行われている → 低リスク（20-30点、LOW/MEDIUM）
- リスク管理体制が適切に機能している → 低リスク（20-30点、LOW/MEDIUM）

【構造的問題がある場合（高リスクスコア: 80-100点）】
1. リスクが認識されているにも関わらず、経営層への報告やエスカレーションが遅延している場合
   → 非常に高いリスクスコア（80-100点、HIGH/HIGH）
2. チャットで懸念が示されているのに、会議では報告されていない場合
   → 報告プロセスの問題として深刻に捉える（80-100点、HIGH/HIGH）
3. 意思決定プロセスの透明性が欠如している場合 → ガバナンス上の問題として評価（80-100点、HIGH/HIGH）
4. 現状維持バイアスが強く、客観的なリスク評価が行われていない場合
   → リスク管理体制の問題として認識（80-100点、HIGH/HIGH）
5. リスク情報が適切に伝達されず、隠蔽されている可能性 → 80-100点、HIGH/HIGH""",
        }
        
        analysis_points = role_specific_analysis_points.get(
            role_id,
            """【分析観点】
1. KPI下方修正の頻度とパターン
2. 撤退/ピボット議論の有無
3. 判断の集中度（発言者の多様性）
4. 反対意見の扱い
5. リスク認識から報告までの遅延"""
        )
        
        prompt = """{role_description}
Helmシステムの一部として、組織の構造的問題を検知し、定量評価を行います。

【役割】
- 会議議事録、チャットログ、会議資料から組織の意思決定プロセスを分析
- 構造的問題パターンを検出（例: B1_正当化フェーズ、ES1_報告遅延、A2_撤退判断の遅れ など）
- 定量評価（0-100点）と説明可能な理由を提供
- 他のロールの視点を想像せず、「あなた自身の立場」から一貫した基準で評価する
- 特に、会議とチャットの内容に差異がある場合（会議では楽観的だがチャットでは懸念が示されているなど）は、それを重要な証拠として評価に反映する

【重要な評価原則】
- **健全な意思決定が行われている場合**: スコアは低く（20-40点）、重要度・緊急度もLOW/MEDIUMになるべき
  - 撤退/ピボット議論が適切に行われている
  - 客観的なデータに基づいた意思決定が行われている
  - リスクが適切に報告されている
  - 会議とチャットの内容が一致している（楽観的な会議、楽観的なチャット）
  - 意思決定プロセスが透明で、多様な意見が反映されている
  
- **構造的問題がある場合**: スコアは高く（80-100点）、重要度・緊急度もHIGHになるべき
  - KPI悪化が続いているのに戦略変更がない
  - 撤退判断が遅れている
  - チャットで懸念が示されているのに会議で反映されない
  - 現状維持バイアスが強く、客観的なリスク評価が行われていない

【入力データ】
- 会議議事録:
{meeting_transcript}

- チャットログ:
{chat_messages}

- 会議資料:
{materials_content}

{analysis_points}

【出力形式】
以下のJSON形式で厳密に回答してください（JSON以外のテキストは含めない）：

【健全な意思決定が行われている場合の例】:
{{
  "findings": [],
  "overall_score": 25,
  "severity": "LOW",
  "urgency": "LOW",
  "explanation": "撤退/ピボット議論が適切に行われており、客観的なデータに基づいた意思決定が行われている。構造的な問題は見られない。"
}}

【構造的問題がある場合の例】:
{{
  "findings": [
    {{
      "pattern_id": "B1_正当化フェーズ",
      "severity": "HIGH",
      "score": 85,
      "description": "問題の説明",
      "evidence": ["証拠1", "証拠2"],
      "quantitative_scores": {{
        "kpi_downgrade_count": 2,
        "exit_discussed": false,
        "decision_concentration_rate": 0.44,
        "ignored_opposition_count": 1
      }}
    }}
  ],
  "overall_score": 85,
  "severity": "HIGH",
  "urgency": "HIGH",
  "explanation": "あなたの立場から見た説明文（2-3文で簡潔に、他のロールの視点を気にせず、あなた自身の評価を述べる）"
}}

**重要**: 健全な意思決定が行われている場合は、findingsを空配列にし、overall_scoreを20-40点、severity/urgencyをLOW/MEDIUMに設定してください。""".format(
            role_description=role_description,
            meeting_transcript=meeting_transcript,
            chat_messages=chat_messages,
            materials_content=materials_content,
            analysis_points=analysis_points,
        )
        return prompt
    
    @staticmethod
    def get_response_schema() -> Dict[str, Any]:
        """
        LLMのレスポンススキーマを取得（Gemini APIのJSON Schema形式）
        
        Returns:
            JSON Schema形式のスキーマ定義
        """
        return {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "pattern_id": {"type": "string"},
                            "severity": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                            "score": {"type": "integer", "minimum": 0, "maximum": 100},
                            "description": {"type": "string"},
                            "evidence": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "quantitative_scores": {
                                "type": "object",
                                "properties": {
                                    "kpi_downgrade_count": {"type": "integer"},
                                    "exit_discussed": {"type": "boolean"},
                                    "decision_concentration_rate": {"type": "number"},
                                    "ignored_opposition_count": {"type": "integer"}
                                }
                            }
                        },
                        "required": ["pattern_id", "severity", "score", "description", "evidence"]
                    }
                },
                "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "severity": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                "urgency": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                "explanation": {"type": "string"}
            },
            "required": ["findings", "overall_score", "severity", "urgency", "explanation"]
        }
