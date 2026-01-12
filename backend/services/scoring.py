"""
重要性・緊急性評価サービス
複数の評価軸によるスコアリングと説明可能な理由生成
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    """重要度レベル"""
    CRITICAL = "CRITICAL"  # 90-100点
    HIGH = "HIGH"          # 70-89点
    MEDIUM = "MEDIUM"      # 40-69点
    LOW = "LOW"            # 0-39点


class UrgencyLevel(str, Enum):
    """緊急度レベル"""
    IMMEDIATE = "IMMEDIATE"  # 即座に対応が必要
    URGENT = "URGENT"        # 24時間以内
    HIGH = "HIGH"            # 1週間以内
    MEDIUM = "MEDIUM"        # 1か月以内
    LOW = "LOW"              # それ以降


class ScoringService:
    """スコアリングサービス"""
    
    def __init__(self):
        """スコアリングサービスの初期化"""
        pass
    
    def evaluate(self, finding: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        構造的問題の重要性・緊急性を評価
        
        Args:
            finding: 検出された構造的問題
            context: コンテキスト情報（会議データ、チャットデータなど）
            
        Returns:
            評価結果（スコア、重要度、緊急度、理由）
        """
        pattern_id = finding.get("pattern_id", "")
        quantitative_scores = finding.get("quantitative_scores", {})
        
        # パターンごとの評価ロジック
        if pattern_id == "B1_正当化フェーズ":
            return self._evaluate_justification_phase(finding, quantitative_scores, context)
        elif pattern_id == "ES1_報告遅延":
            return self._evaluate_escalation_delay(finding, quantitative_scores, context)
        else:
            return self._evaluate_generic(finding, quantitative_scores, context)
    
    def _evaluate_justification_phase(
        self, 
        finding: Dict[str, Any], 
        quantitative_scores: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """正当化フェーズの評価"""
        kpi_downgrade_count = quantitative_scores.get("kpi_downgrade_count", 0)
        decision_concentration_rate = quantitative_scores.get("decision_concentration_rate", 0)
        ignored_opposition_count = quantitative_scores.get("ignored_opposition_count", 0)
        
        # 重要性スコア（0-100）
        importance_score = 0
        
        # KPI下方修正の回数による重要度（デモ用にスコアを上げる）
        if kpi_downgrade_count >= 3:
            importance_score += 50
        elif kpi_downgrade_count >= 2:
            importance_score += 40  # デモ用に30→40に上げる
        elif kpi_downgrade_count >= 1:
            importance_score += 25  # デモ用に15→25に上げる
        
        # 判断集中率による重要度（デモ用にスコアを上げる）
        if decision_concentration_rate >= 0.8:
            importance_score += 35  # デモ用に30→35に上げる
        elif decision_concentration_rate >= 0.7:
            importance_score += 30  # デモ用に20→30に上げる
        elif decision_concentration_rate >= 0.5:
            importance_score += 15  # デモ用に10→15に上げる
        
        # 反対意見の無視による重要度（デモ用にスコアを上げる）
        if ignored_opposition_count >= 2:
            importance_score += 25  # デモ用に20→25に上げる
        elif ignored_opposition_count >= 1:
            importance_score += 15  # デモ用に10→15に上げる
        
        # 緊急度スコア（0-100）
        urgency_score = 0
        
        # KPI下方修正の頻度による緊急度
        if kpi_downgrade_count >= 3:
            urgency_score += 40  # 複数回の下方修正は緊急
        elif kpi_downgrade_count >= 2:
            urgency_score += 25
        
        # 判断集中率による緊急度（デモ用にスコアを上げる）
        if decision_concentration_rate >= 0.8:
            urgency_score += 40  # デモ用に30→40に上げる
        elif decision_concentration_rate >= 0.7:
            urgency_score += 30  # デモ用に20→30に上げる
        
        # 反対意見の無視による緊急度（デモ用にスコアを上げる）
        if ignored_opposition_count >= 2:
            urgency_score += 25  # デモ用に20→25に上げる
        elif ignored_opposition_count >= 1:
            urgency_score += 15  # デモ用に追加
        
        # 総合スコア（重要性と緊急度の加重平均）
        overall_score = int((importance_score * 0.6 + urgency_score * 0.4))
        
        # 重要度レベルの判定
        if overall_score >= 90:
            severity = SeverityLevel.CRITICAL
        elif overall_score >= 70:
            severity = SeverityLevel.HIGH
        elif overall_score >= 40:
            severity = SeverityLevel.MEDIUM
        else:
            severity = SeverityLevel.LOW
        
        # 緊急度レベルの判定
        if urgency_score >= 80:
            urgency = UrgencyLevel.IMMEDIATE
        elif urgency_score >= 60:
            urgency = UrgencyLevel.URGENT
        elif urgency_score >= 40:
            urgency = UrgencyLevel.HIGH
        elif urgency_score >= 20:
            urgency = UrgencyLevel.MEDIUM
        else:
            urgency = UrgencyLevel.LOW
        
        # 説明可能な理由の生成
        reasons = []
        if kpi_downgrade_count >= 2:
            reasons.append(f"KPI下方修正が{kpi_downgrade_count}回繰り返されており、戦略見直しの必要性が高い")
        if decision_concentration_rate >= 0.7:
            reasons.append(f"判断が特定の人物に集中しており（集中率: {decision_concentration_rate:.1%}）、意思決定の多様性が欠如している")
        if ignored_opposition_count >= 1:
            reasons.append(f"反対意見が{ignored_opposition_count}件無視されており、組織の学習能力が低下している")
        
        explanation = " ".join(reasons) if reasons else "構造的問題が検出されました。"
        
        return {
            "overall_score": overall_score,
            "importance_score": importance_score,
            "urgency_score": urgency_score,
            "severity": severity.value,
            "urgency": urgency.value,
            "reasons": reasons,
            "explanation": explanation,
            "quantitative_breakdown": {
                "kpi_downgrade_impact": kpi_downgrade_count * 10,
                "decision_concentration_impact": int(decision_concentration_rate * 30),
                "opposition_ignored_impact": ignored_opposition_count * 10
            }
        }
    
    def _evaluate_escalation_delay(
        self,
        finding: Dict[str, Any],
        quantitative_scores: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """エスカレーション遅延の評価"""
        # 簡易的な評価（実際の実装ではより詳細に）
        overall_score = finding.get("score", 65)
        
        if overall_score >= 70:
            severity = SeverityLevel.HIGH
            urgency = UrgencyLevel.URGENT
        elif overall_score >= 40:
            severity = SeverityLevel.MEDIUM
            urgency = UrgencyLevel.HIGH
        else:
            severity = SeverityLevel.LOW
            urgency = UrgencyLevel.MEDIUM
        
        return {
            "overall_score": overall_score,
            "importance_score": overall_score,
            "urgency_score": overall_score,
            "severity": severity.value,
            "urgency": urgency.value,
            "reasons": ["リスク認識から報告までの遅延が検出されました。"],
            "explanation": "現場でリスクが認識されていますが、上位への報告が行われていません。",
            "quantitative_breakdown": {}
        }
    
    def _evaluate_generic(
        self,
        finding: Dict[str, Any],
        quantitative_scores: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """汎用的な評価"""
        overall_score = finding.get("score", 50)
        
        if overall_score >= 70:
            severity = SeverityLevel.HIGH
            urgency = UrgencyLevel.HIGH
        elif overall_score >= 40:
            severity = SeverityLevel.MEDIUM
            urgency = UrgencyLevel.MEDIUM
        else:
            severity = SeverityLevel.LOW
            urgency = UrgencyLevel.LOW
        
        return {
            "overall_score": overall_score,
            "importance_score": overall_score,
            "urgency_score": overall_score,
            "severity": severity.value,
            "urgency": urgency.value,
            "reasons": [finding.get("description", "構造的問題が検出されました。")],
            "explanation": finding.get("description", "構造的問題が検出されました。"),
            "quantitative_breakdown": {}
        }

