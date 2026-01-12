"""
Vertex AI / Gemini統合（実際のAPI実装）
環境変数が設定されている場合に使用
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os

try:
    from google.cloud import aiplatform
    from vertexai.preview.generative_models import GenerativeModel
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False


class VertexAIRealService:
    """Vertex AIサービス（実際のAPI実装）"""
    
    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1"):
        """
        Args:
            project_id: Google Cloud Project ID
            location: Vertex AIのリージョン
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        self.location = location
        
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT_ID環境変数が設定されていません")
        
        if not VERTEX_AI_AVAILABLE:
            raise ImportError("google-cloud-aiplatformがインストールされていません")
        
        # Vertex AIの初期化
        aiplatform.init(project=self.project_id, location=self.location)
        self.model = GenerativeModel("gemini-pro")
    
    def analyze_structure(self, meeting_data: Dict[str, Any], chat_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        構造的問題をAIで分析
        
        Args:
            meeting_data: 会議データ（パース済み）
            chat_data: チャットデータ（パース済み、オプション）
            
        Returns:
            分析結果
        """
        # プロンプトの構築
        prompt = self._build_analysis_prompt(meeting_data, chat_data)
        
        try:
            # Gemini APIで分析
            response = self.model.generate_content(prompt)
            analysis_text = response.text
            
            # レスポンスをパース（実際の実装ではJSON形式で返すようにプロンプトを調整）
            findings = self._parse_ai_response(analysis_text, meeting_data, chat_data)
            
            return {
                "findings": findings,
                "overall_score": max([f.get("score", 0) for f in findings], default=0),
                "severity": "HIGH" if any(f.get("score", 0) >= 70 for f in findings) else "MEDIUM",
                "explanation": analysis_text,
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            # エラーが発生した場合はモックにフォールバック
            print(f"Vertex AI分析エラー: {e}")
            return self._fallback_analysis(meeting_data, chat_data)
    
    def _build_analysis_prompt(self, meeting_data: Dict[str, Any], chat_data: Optional[Dict[str, Any]]) -> str:
        """分析用プロンプトを構築"""
        prompt = """あなたは組織の意思決定プロセスを分析するAIです。
以下の会議データとチャットデータから、構造的問題を検出してください。

【会議データ】
"""
        # 会議データの要約
        statements = meeting_data.get("statements", [])
        kpi_mentions = meeting_data.get("kpi_mentions", [])
        exit_discussed = meeting_data.get("exit_discussed", False)
        
        prompt += f"- 発言数: {len(statements)}\n"
        prompt += f"- KPI言及: {len(kpi_mentions)}回\n"
        prompt += f"- 撤退議論: {'あり' if exit_discussed else 'なし'}\n"
        
        if chat_data:
            prompt += "\n【チャットデータ】\n"
            prompt += f"- メッセージ数: {chat_data.get('total_messages', 0)}\n"
            prompt += f"- リスクメッセージ: {len(chat_data.get('risk_messages', []))}件\n"
            prompt += f"- 反対意見: {len(chat_data.get('opposition_messages', []))}件\n"
        
        prompt += """
【検出すべきパターン】
1. B1_正当化フェーズ: KPI悪化が認識されているが、戦略変更議論がない
2. ES1_報告遅延: リスク認識があるが、エスカレーションが行われていない

各パターンについて、以下をJSON形式で返してください:
- pattern_id: パターンID
- severity: HIGH/MEDIUM/LOW
- score: 0-100のスコア
- description: 問題の説明
- evidence: 証拠のリスト
"""
        
        return prompt
    
    def _parse_ai_response(self, response_text: str, meeting_data: Dict[str, Any], chat_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """AIレスポンスをパース"""
        # 実際の実装では、JSON形式で返すようにプロンプトを調整
        # ここでは簡易的なパース（実際の実装ではより堅牢に）
        findings = []
        
        # 正当化フェーズの検出（簡易版）
        kpi_mentions = meeting_data.get("kpi_mentions", [])
        exit_discussed = meeting_data.get("exit_discussed", False)
        
        if len(kpi_mentions) >= 2 and not exit_discussed:
            findings.append({
                "pattern_id": "B1_正当化フェーズ",
                "severity": "HIGH",
                "score": 75,
                "description": "KPI悪化認識があるが戦略変更議論がない",
                "evidence": [
                    f"KPI下方修正が{len(kpi_mentions)}回検出",
                    "撤退/ピボット議論が一度も行われていない"
                ]
            })
        
        return findings
    
    def _fallback_analysis(self, meeting_data: Dict[str, Any], chat_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """フォールバック分析（モック）"""
        findings = []
        
        kpi_mentions = meeting_data.get("kpi_mentions", [])
        exit_discussed = meeting_data.get("exit_discussed", False)
        
        if len(kpi_mentions) >= 2 and not exit_discussed:
            findings.append({
                "pattern_id": "B1_正当化フェーズ",
                "severity": "HIGH",
                "score": 75,
                "description": "KPI悪化認識があるが戦略変更議論がない",
                "evidence": [
                    f"KPI下方修正が{len(kpi_mentions)}回検出",
                    "撤退/ピボット議論が一度も行われていない"
                ]
            })
        
        return {
            "findings": findings,
            "overall_score": 75 if findings else 0,
            "severity": "HIGH" if findings else "LOW",
            "explanation": "Vertex AI分析中にエラーが発生しました。フォールバック分析を使用しています。",
            "created_at": datetime.now().isoformat()
        }
    
    def generate_explanation(self, findings: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        説明文を生成
        
        Args:
            findings: 検出された構造的問題
            context: コンテキスト情報
            
        Returns:
            説明文
        """
        if not findings:
            return "構造的問題は検出されませんでした。"
        
        prompt = f"""以下の構造的問題について、Executive向けに分かりやすく説明してください:

{findings}

説明は以下の点を含めてください:
- 問題の本質
- なぜ問題なのか
- 放置した場合のリスク
- 推奨される対応
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"説明文生成エラー: {e}")
            return self._fallback_explanation(findings)
    
    def _fallback_explanation(self, findings: List[Dict[str, Any]]) -> str:
        """フォールバック説明文"""
        finding = findings[0]
        pattern_id = finding.get("pattern_id", "")
        
        if pattern_id == "B1_正当化フェーズ":
            return (
                "現在の会議構造は「正当化フェーズ」に入っています。"
                "数値悪化は共有されていますが、戦略変更を提案する主体と"
                "「やめる」という選択肢が構造的に排除されています。"
            )
        else:
            return f"構造的問題が検出されました: {pattern_id}"

