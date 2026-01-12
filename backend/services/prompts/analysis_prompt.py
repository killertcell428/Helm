"""
分析用プロンプト生成
構造的問題検知のためのプロンプトを構築
"""

from typing import Dict, Any, Optional


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
        # 会議議事録のテキストを取得
        meeting_transcript = meeting_data.get("transcript", "")
        if not meeting_transcript and meeting_data.get("statements"):
            # パース済みデータから議事録を再構築
            statements = meeting_data.get("statements", [])
            meeting_transcript = "\n".join([
                f"{stmt.get('speaker', 'Unknown')}: {stmt.get('text', '')}"
                for stmt in statements
            ])
        
        # チャットログのテキストを取得
        chat_messages = ""
        if chat_data:
            messages = chat_data.get("messages", [])
            if messages:
                chat_messages = "\n".join([
                    f"{msg.get('author', 'Unknown')}: {msg.get('text', '')}"
                    for msg in messages
                ])
        
        # 会議資料のテキストを取得
        materials_content = ""
        if materials_data:
            materials_content = materials_data.get("content", "")
        
        # プロンプトテンプレート
        prompt = """あなたは組織の意思決定プロセスを分析する専門AIです。
Helmシステムの一部として、組織の構造的問題を検知し、定量評価を行います。

【役割】
- 会議議事録、チャットログ、会議資料から組織の意思決定プロセスを分析
- 構造的問題パターンを検出（例: B1_正当化フェーズ、ES1_報告遅延）
- 定量評価（0-100点）と説明可能な理由を提供

【入力データ】
- 会議議事録:
{meeting_transcript}

- チャットログ:
{chat_messages}

- 会議資料:
{materials_content}

【分析観点】
1. KPI下方修正の頻度とパターン
2. 撤退/ピボット議論の有無
3. 判断の集中度（発言者の多様性）
4. 反対意見の扱い
5. リスク認識から報告までの遅延

【出力形式】
以下のJSON形式で厳密に回答してください（JSON以外のテキストは含めない）：
{{
  "findings": [
    {{
      "pattern_id": "B1_正当化フェーズ",
      "severity": "HIGH|MEDIUM|LOW",
      "score": 0-100,
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
  "overall_score": 75,
  "severity": "HIGH",
  "urgency": "HIGH|MEDIUM|LOW",
  "explanation": "Executive向けの説明文（2-3文で簡潔に）"
}}""".format(
            meeting_transcript=meeting_transcript or "（議事録なし）",
            chat_messages=chat_messages or "（チャットログなし）",
            materials_content=materials_content or "（会議資料なし）"
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
