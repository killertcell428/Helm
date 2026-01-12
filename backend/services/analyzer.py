"""
構造的問題検知サービス
正当化フェーズパターンの検出
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import re
from .scoring import ScoringService


class StructureAnalyzer:
    """構造的問題検知アナライザー"""
    
    def __init__(self, use_vertex_ai: bool = False, vertex_ai_service=None, scoring_service=None):
        """
        Args:
            use_vertex_ai: Vertex AIを使用するか（Falseの場合はルールベース）
            vertex_ai_service: Vertex AIサービスインスタンス（オプション）
            scoring_service: スコアリングサービスインスタンス（オプション）
        """
        self.use_vertex_ai = use_vertex_ai
        self.vertex_ai_service = vertex_ai_service
        self.scoring_service = scoring_service or ScoringService()
    
    def analyze(self, meeting_data: Dict[str, Any], chat_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        構造的問題を検知
        
        Args:
            meeting_data: 会議データ（パース済み）
            chat_data: チャットデータ（パース済み、オプション）
            
        Returns:
            分析結果
        """
        if self.use_vertex_ai:
            # TODO: Vertex AI / Geminiで分析
            return self._analyze_with_vertex_ai(meeting_data, chat_data)
        else:
            return self._analyze_with_rules(meeting_data, chat_data)
    
    def _analyze_with_rules(self, meeting_data: Dict[str, Any], chat_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """ルールベース分析"""
        findings = []
        scores = {}
        
        # KPI下方修正の検出
        kpi_mentions = meeting_data.get("kpi_mentions", [])
        kpi_downgrade_count = sum(
            1 for mention in kpi_mentions
            if any(keyword in mention["text"] for keyword in ["下方修正", "下回", "未達", "▲"])
        )
        
        # 撤退/ピボット議論の不在
        exit_discussed = meeting_data.get("exit_discussed", False)
        
        # 判断集中の検出（発言者の多様性）
        statements = meeting_data.get("statements", [])
        speakers = [stmt["speaker"] for stmt in statements]
        if len(statements) == 0:
            decision_concentration_rate = 0.0
        else:
            # 最も多く発言した人の発言数 / 総発言数
            from collections import Counter
            speaker_counts = Counter(speakers)
            max_speaker_count = max(speaker_counts.values())
            decision_concentration_rate = max_speaker_count / len(statements)  # len(speakers)ではなくlen(statements)
        
        # 反対意見の無視
        ignored_opposition_count = 0
        if chat_data:
            opposition_messages = chat_data.get("opposition_messages", [])
            # チャットで反対意見が出ているが、会議で反映されていない
            if opposition_messages and not exit_discussed:
                ignored_opposition_count = len(opposition_messages)
        
        # 正当化フェーズパターンの検出（判断集中率の条件を緩和）
        # KPI下方修正が2回以上あり、撤退議論がなく、判断が集中している場合
        if (kpi_downgrade_count >= 2 and 
            not exit_discussed and 
            decision_concentration_rate >= 0.4):  # 0.5から0.4にさらに緩和（デモ用）
            
            score = 75  # 閾値70を超過
            severity = "HIGH"
            
            findings.append({
                "pattern_id": "B1_正当化フェーズ",
                "severity": severity,
                "score": score,
                "description": "KPI悪化認識があるが戦略変更議論がない",
                "evidence": [
                    f"KPI下方修正が{kpi_downgrade_count}回検出",
                    "撤退/ピボット議論が一度も行われていない",
                    f"判断集中率: {decision_concentration_rate:.2%}",
                    f"反対意見無視: {ignored_opposition_count}件"
                ],
                "quantitative_scores": {
                    "kpi_downgrade_count": kpi_downgrade_count,
                    "exit_discussed": exit_discussed,
                    "decision_concentration_rate": decision_concentration_rate,
                    "ignored_opposition_count": ignored_opposition_count
                }
            })
            
            scores["B1_正当化フェーズ"] = score
        
        # エスカレーション遅延の検出
        if chat_data:
            risk_messages = chat_data.get("risk_messages", [])
            escalation_mentioned = chat_data.get("escalation_mentioned", False)
            
            if risk_messages and not escalation_mentioned and decision_concentration_rate < 0.5:
                score = 65
                severity = "MEDIUM"
                
                findings.append({
                    "pattern_id": "ES1_報告遅延",
                    "severity": severity,
                    "score": score,
                    "description": "リスク認識があるが報告が遅延している",
                    "evidence": [
                        f"リスク提起メッセージ: {len(risk_messages)}件",
                        "エスカレーション未完了"
                    ]
                })
        
        # 重要性・緊急性評価を実行
        evaluated_findings = []
        for finding in findings:
            evaluation = self.scoring_service.evaluate(finding, {
                "meeting_data": meeting_data,
                "chat_data": chat_data
            })
            
            # 評価結果をfindingに追加
            finding["evaluation"] = evaluation
            finding["score"] = evaluation["overall_score"]
            finding["severity"] = evaluation["severity"]
            finding["urgency"] = evaluation["urgency"]
            finding["importance_score"] = evaluation["importance_score"]
            finding["urgency_score"] = evaluation["urgency_score"]
            finding["reasons"] = evaluation["reasons"]
            
            evaluated_findings.append(finding)
        
        # 全体スコアの計算（最高スコアを使用）
        overall_score = max([f["score"] for f in evaluated_findings], default=0)
        overall_severity = "HIGH" if overall_score >= 70 else "MEDIUM" if overall_score >= 40 else "LOW"
        
        # 最も緊急度の高いfindingの緊急度を使用
        max_urgency = max([f.get("urgency", "LOW") for f in evaluated_findings], default="LOW", key=lambda x: {
            "IMMEDIATE": 5, "URGENT": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1
        }.get(x, 1))
        
        return {
            "findings": evaluated_findings,
            "scores": scores,
            "overall_score": overall_score,
            "severity": overall_severity,
            "urgency": max_urgency,
            "explanation": self._generate_explanation(evaluated_findings, overall_score),
            "created_at": datetime.now().isoformat()
        }
    
    def _analyze_with_vertex_ai(self, meeting_data: Dict[str, Any], chat_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Vertex AI / Geminiで分析"""
        if self.vertex_ai_service:
            return self.vertex_ai_service.analyze_structure(meeting_data, chat_data)
        else:
            # Vertex AIサービスが設定されていない場合はルールベースにフォールバック
            return self._analyze_with_rules(meeting_data, chat_data)
    
    def _generate_explanation(self, findings: List[Dict[str, Any]], score: int) -> str:
        """説明文を生成"""
        if not findings:
            return "構造的問題は検出されませんでした。"
        
        finding = findings[0]  # 最初の検出結果を使用
        pattern_id = finding.get("pattern_id", "")
        evidence = finding.get("evidence", [])
        evaluation = finding.get("evaluation", {})
        reasons = evaluation.get("reasons", [])
        
        # 評価結果から説明文を生成
        if reasons:
            explanation = f"【重要度: {evaluation.get('severity', 'MEDIUM')} / 緊急度: {evaluation.get('urgency', 'MEDIUM')}】\n\n"
            explanation += " ".join(reasons)
            if evidence:
                explanation += f"\n\n証拠: {', '.join(evidence[:3])}"
        else:
            # フォールバック: 従来の説明文生成
            if pattern_id == "B1_正当化フェーズ":
                explanation = (
                    f"現在の会議構造は「正当化フェーズ」に入っています（スコア: {score}点）。"
                    f"数値悪化は共有されていますが、戦略変更を提案する主体と"
                    f"「やめる」という選択肢が構造的に排除されています。"
                    f"証拠: {', '.join(evidence[:2])}"
                )
            elif pattern_id == "ES1_報告遅延":
                explanation = (
                    f"リスク認識から報告までの遅延が検出されました（スコア: {score}点）。"
                    f"現場でリスクが認識されていますが、上位への報告が行われていません。"
                )
            else:
                explanation = f"構造的問題が検出されました（スコア: {score}点）。"
        
        return explanation

