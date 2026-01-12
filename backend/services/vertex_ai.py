"""
Vertex AI / Gemini統合
構造的問題検知と説明文生成
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os


class VertexAIService:
    """Vertex AIサービス"""
    
    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1"):
        """
        Args:
            project_id: Google Cloud Project ID
            location: Vertex AIのリージョン
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        self.location = location
        self.use_mock = self.project_id is None
        
        # 実際のAPIが利用可能かチェック
        self._check_vertex_ai_availability()
    
    def _check_vertex_ai_availability(self):
        """Vertex AIが利用可能かチェック"""
        if not self.use_mock:
            try:
                from google.cloud import aiplatform
                self._vertex_ai_available = True
            except ImportError:
                print("警告: google-cloud-aiplatformがインストールされていません。モックモードを使用します。")
                self.use_mock = True
                self._vertex_ai_available = False
        else:
            self._vertex_ai_available = False
    
    def analyze_structure(self, meeting_data: Dict[str, Any], chat_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        構造的問題をAIで分析
        
        Args:
            meeting_data: 会議データ（パース済み）
            chat_data: チャットデータ（パース済み、オプション）
            
        Returns:
            分析結果
        """
        if self.use_mock or not self._vertex_ai_available:
            return self._mock_analyze(meeting_data, chat_data)
        
        # Vertex AI / Geminiで実際に分析
        try:
            from google.cloud import aiplatform
            from vertexai.preview.generative_models import GenerativeModel
            
            # Vertex AIの初期化
            aiplatform.init(project=self.project_id, location=self.location)
            model = GenerativeModel("gemini-pro")
            
            # プロンプトの構築
            prompt = self._build_analysis_prompt(meeting_data, chat_data)
            
            # Gemini APIで分析
            response = model.generate_content(prompt)
            analysis_text = response.text
            
            # レスポンスをパース
            findings = self._parse_ai_response(analysis_text, meeting_data, chat_data)
            
            return {
                "findings": findings,
                "overall_score": max([f.get("score", 0) for f in findings], default=0),
                "severity": "HIGH" if any(f.get("score", 0) >= 70 for f in findings) else "MEDIUM",
                "explanation": analysis_text,
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Vertex AI分析エラー: {e}")
            # エラーが発生した場合はモックにフォールバック
            return self._mock_analyze(meeting_data, chat_data)
    
    def _mock_analyze(self, meeting_data: Dict[str, Any], chat_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """モック分析結果（実際のAI分析のプレースホルダー）"""
        # 実際の実装では、ここでGemini APIを呼び出す
        findings = []
        
        # 正当化フェーズの検出
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
            "explanation": self._generate_explanation(findings),
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
        if self.use_mock:
            return self._generate_explanation(findings)
        
        # TODO: Gemini APIで説明文を生成
        # prompt = f"以下の構造的問題について、Executive向けに説明してください: {findings}"
        # model = GenerativeModel("gemini-pro")
        # response = model.generate_content(prompt)
        # return response.text
        
        return self._generate_explanation(findings)
    
    def _build_analysis_prompt(self, meeting_data: Dict[str, Any], chat_data: Optional[Dict[str, Any]]) -> str:
        """分析用プロンプトを構築"""
        prompt = """あなたは組織の意思決定プロセスを分析するAIです。
以下の会議データとチャットデータから、構造的問題を検出してください。

【会議データ】
"""
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
        
        prompt += "\n検出すべきパターン: B1_正当化フェーズ（KPI悪化認識があるが戦略変更議論がない）"
        return prompt
    
    def _parse_ai_response(self, response_text: str, meeting_data: Dict[str, Any], chat_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """AIレスポンスをパース（簡易版）"""
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
        
        return findings
    
    def _generate_explanation(self, findings: List[Dict[str, Any]]) -> str:
        """モック説明文生成"""
        if not findings:
            return "構造的問題は検出されませんでした。"
        
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

