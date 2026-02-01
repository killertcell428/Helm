"""
エスカレーション判断エンジン
スコアに基づいてExecutiveを自動的に呼び出す
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os


class EscalationEngine:
    """エスカレーション判断エンジン"""
    
    def __init__(self, escalation_threshold: int = 50):
        """
        Args:
            escalation_threshold: エスカレーション閾値（スコア）
        """
        self.escalation_threshold = escalation_threshold
        self.demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"  # デモモード
    
    def should_escalate(self, analysis_result: Dict[str, Any]) -> bool:
        """
        エスカレーションが必要か判断
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            エスカレーションが必要な場合True
        """
        # analysis_dataの構造に対応: score, overall_score, ensemble.overall_score の順で確認
        overall_score = analysis_result.get("overall_score", 0)
        if overall_score == 0:
            overall_score = analysis_result.get("score", 0)
        if overall_score == 0:
            ensemble = analysis_result.get("ensemble", {})
            if isinstance(ensemble, dict):
                overall_score = ensemble.get("overall_score", 0)
        
        severity = analysis_result.get("severity", "LOW")
        if not severity or severity == "LOW":
            ensemble = analysis_result.get("ensemble", {})
            if isinstance(ensemble, dict):
                severity = ensemble.get("severity", severity)
        
        # スコアが閾値を超えている場合、または重要度がHIGHの場合
        if overall_score >= self.escalation_threshold:
            return True
        
        if severity == "HIGH" or severity == "CRITICAL":
            return True
        
        # デモ用: findingsがある場合は常にエスカレーション（デモを確実に動作させるため）
        if self.demo_mode:
            findings = analysis_result.get("findings", [])
            if findings and len(findings) > 0:
                # デモ用のフォールバック: 構造的問題が検出されていればエスカレーション
                return True
        
        return False
    
    def determine_target_role(self, analysis_result: Dict[str, Any]) -> str:
        """
        エスカレーション先のロールを決定
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            ターゲットロール（現在は常に"Executive"）
        """
        # 将来的には、組織グラフを参照して適切なロールを決定
        # 現在は常にExecutiveにエスカレーション
        return "Executive"
    
    def generate_escalation_reason(self, analysis_result: Dict[str, Any]) -> str:
        """
        エスカレーション理由を生成
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            エスカレーション理由
        """
        findings = analysis_result.get("findings", [])
        
        # analysis_dataの構造に対応: score, overall_score, ensemble.overall_score の順で確認
        overall_score = analysis_result.get("overall_score", 0)
        if overall_score == 0:
            overall_score = analysis_result.get("score", 0)
        if overall_score == 0:
            ensemble = analysis_result.get("ensemble", {})
            if isinstance(ensemble, dict):
                overall_score = ensemble.get("overall_score", 0)
        
        severity = analysis_result.get("severity", "LOW")
        urgency = analysis_result.get("urgency", "MEDIUM")
        
        # ensembleからも取得を試みる
        ensemble = analysis_result.get("ensemble", {})
        if isinstance(ensemble, dict):
            if not severity or severity == "LOW":
                severity = ensemble.get("severity", severity)
            if not urgency or urgency == "LOW":
                urgency = ensemble.get("urgency", urgency)
        
        if not findings:
            return "構造的問題が検出されました。"
        
        finding = findings[0]
        pattern_id = finding.get("pattern_id", "")
        
        reason_parts = []
        
        # パターンに基づく理由
        if pattern_id == "B1_正当化フェーズ":
            reason_parts.append("正当化フェーズの兆候が検出されました。")
        elif pattern_id == "ES1_報告遅延":
            reason_parts.append("エスカレーション遅延が検出されました。")
        else:
            reason_parts.append("構造的問題が検出されました。")
        
        # スコアと重要度に基づく理由
        reason_parts.append(f"スコア: {overall_score}点（重要度: {severity}, 緊急度: {urgency}）")
        reason_parts.append("構造的変更にはExecutiveの承認が必要です。")
        
        return " ".join(reason_parts)
    
    def create_escalation(self, analysis_id: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        エスカレーションを作成
        
        Args:
            analysis_id: 分析ID
            analysis_result: 分析結果
            
        Returns:
            エスカレーションデータ
        """
        if not self.should_escalate(analysis_result):
            return None
        
        target_role = self.determine_target_role(analysis_result)
        reason = self.generate_escalation_reason(analysis_result)
        
        # analysis_dataの構造に対応: overall_score > score > ensemble.overall_score の順で確認
        overall_score = analysis_result.get("overall_score", 0)
        if overall_score == 0:
            overall_score = analysis_result.get("score", 0)
        if overall_score == 0:
            ensemble = analysis_result.get("ensemble", {})
            if isinstance(ensemble, dict):
                overall_score = ensemble.get("overall_score", 0)
        
        # スコアを数値に変換（文字列の場合に対応）
        try:
            overall_score = int(float(overall_score))
        except (ValueError, TypeError):
            overall_score = 0
        
        severity = analysis_result.get("severity", "MEDIUM")
        urgency = analysis_result.get("urgency", "MEDIUM")
        
        # ensembleからも取得を試みる
        ensemble = analysis_result.get("ensemble", {})
        if isinstance(ensemble, dict):
            if not severity or severity == "LOW":
                severity = ensemble.get("severity", severity)
            if not urgency or urgency == "LOW":
                urgency = ensemble.get("urgency", urgency)
        
        return {
            "analysis_id": analysis_id,
            "target_role": target_role,
            "reason": reason,
            "severity": severity,
            "urgency": urgency,
            "score": overall_score,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }

