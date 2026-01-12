"""
タスク生成用プロンプト生成
Executive承認に基づいて実行可能なタスクを生成するためのプロンプトを構築
"""

from typing import Dict, Any, Optional
import json


class TaskGenerationPromptBuilder:
    """タスク生成用プロンプトビルダー"""
    
    @staticmethod
    def build(
        analysis_result: Dict[str, Any],
        approval_data: Dict[str, Any],
        approved_interventions: Optional[list] = None
    ) -> str:
        """
        タスク生成用プロンプトを構築
        
        Args:
            analysis_result: 分析結果
            approval_data: Executive承認データ
            approved_interventions: 承認された介入案（オプション）
            
        Returns:
            プロンプト文字列
        """
        # 分析結果のサマリーを取得
        findings_summary = []
        for finding in analysis_result.get("findings", []):
            findings_summary.append({
                "pattern_id": finding.get("pattern_id", ""),
                "description": finding.get("description", ""),
                "severity": finding.get("severity", "MEDIUM"),
                "score": finding.get("score", 0)
            })
        
        # Executive承認内容を取得
        decision = approval_data.get("decision", "approve")
        modifications = approval_data.get("modifications")
        
        # 承認された介入案を取得
        interventions_text = ""
        if approved_interventions:
            interventions_text = "\n".join([
                f"- {intervention}"
                for intervention in approved_interventions
            ])
        elif modifications:
            # modificationsから介入案を抽出
            if isinstance(modifications, str):
                interventions_text = modifications
            elif isinstance(modifications, list):
                interventions_text = "\n".join([
                    f"- {mod}"
                    for mod in modifications
                ])
        
        # プロンプトテンプレート
        prompt = """あなたは組織の意思決定を支援するAIエージェントです。
Helmシステムの一部として、Executive承認に基づいて実行可能なタスクを生成します。

【役割】
- 分析結果とExecutive承認内容から、具体的な実行タスクを設計
- タスクの依存関係を考慮
- 各タスクの実行方法と期待される成果物を明確化

【入力データ】
- 分析結果:
{analysis_result_json}

- Executive承認内容:
- 決定: {decision}
- 修正内容: {modifications}

- 承認された介入案:
{interventions}

【タスク設計の原則】
1. 分析結果で検出された問題に対応する
2. Executive承認内容を反映する
3. 実行可能で具体的なタスクにする
4. 依存関係を明確にする（例: データ分析 → 資料生成 → 通知）

【出力形式】
以下のJSON形式で厳密に回答してください（JSON以外のテキストは含めない）：
{{
  "tasks": [
    {{
      "id": "task1",
      "name": "タスク名（具体的で実行可能）",
      "type": "research|analysis|document|notification|calendar",
      "description": "タスクの詳細説明（何を、なぜ、どのように）",
      "dependencies": [],
      "estimated_duration": "2時間",
      "expected_output": "期待される成果物の説明"
    }}
  ],
  "execution_plan": {{
    "total_tasks": 5,
    "estimated_total_duration": "8時間",
    "critical_path": ["task1", "task3", "task5"]
  }}
}}""".format(
            analysis_result_json=json.dumps(findings_summary, ensure_ascii=False, indent=2),
            decision=decision,
            modifications=modifications or "なし",
            interventions=interventions_text or "なし"
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
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": ["research", "analysis", "document", "notification", "calendar"]
                            },
                            "description": {"type": "string"},
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "estimated_duration": {"type": "string"},
                            "expected_output": {"type": "string"}
                        },
                        "required": ["id", "name", "type", "description"]
                    }
                },
                "execution_plan": {
                    "type": "object",
                    "properties": {
                        "total_tasks": {"type": "integer"},
                        "estimated_total_duration": {"type": "string"},
                        "critical_path": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["total_tasks", "estimated_total_duration"]
                }
            },
            "required": ["tasks", "execution_plan"]
        }
