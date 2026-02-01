"""
確信度に基づくエスカレーション機能
確信度が低い時は「質問として投げる」
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from utils.logger import logger
from utils.exceptions import ServiceError


class ConfidenceLevel(str, Enum):
    """確信度レベル"""
    HIGH = "high"  # 80%以上
    MEDIUM = "medium"  # 60-80%
    LOW = "low"  # 60%未満


class ConfidenceBasedEscalation:
    """確信度に基づくエスカレーション"""
    
    # 確信度の閾値
    CONFIDENCE_THRESHOLDS = {
        ConfidenceLevel.HIGH: 0.8,
        ConfidenceLevel.MEDIUM: 0.6,
        ConfidenceLevel.LOW: 0.0
    }
    
    def __init__(self):
        """初期化"""
        pass
    
    def calculate_confidence(
        self,
        analysis_result: Dict[str, Any]
    ) -> float:
        """
        確信度を計算（エラーハンドリング付き）
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            確信度（0.0-1.0、エラー時は0.0）
        """
        try:
            if not analysis_result or not isinstance(analysis_result, dict):
                logger.warning("Invalid analysis_result, returning 0.0 confidence")
                return 0.0
            
            # ルールベーススコアとLLMスコアの差が小さいほど確信度が高い
            rule_score = analysis_result.get("rule_score", 0)
            llm_score = analysis_result.get("llm_score", 0)
            
            # スコアを数値に変換
            try:
                rule_score = float(rule_score) if rule_score else 0.0
                llm_score = float(llm_score) if llm_score else 0.0
            except (ValueError, TypeError):
                logger.warning(f"Invalid score values: rule={rule_score}, llm={llm_score}")
                rule_score = 0.0
                llm_score = 0.0
            
            if rule_score == 0 and llm_score == 0:
                return 0.0
            
            # スコアの差を計算
            score_diff = abs(rule_score - llm_score)
            max_score = max(rule_score, llm_score, 1.0)
            
            # 差が小さいほど確信度が高い
            confidence = 1.0 - (score_diff / max_score)
            
            # ロール視点の評価が一致しているかも考慮
            try:
                ensemble = analysis_result.get("ensemble", {})
                if isinstance(ensemble, dict):
                    contributing_roles = ensemble.get("contributing_roles", [])
                    if contributing_roles and isinstance(contributing_roles, list):
                        # 各ロールの評価のばらつきを計算
                        scores = []
                        for r in contributing_roles:
                            if isinstance(r, dict):
                                score = r.get("overall_score", 0)
                                try:
                                    scores.append(float(score) if score else 0.0)
                                except (ValueError, TypeError):
                                    continue
                        
                        if scores:
                            score_variance = self._calculate_variance(scores)
                            max_variance = 100.0  # スコアの最大範囲
                            variance_penalty = min(score_variance / max_variance, 0.3)  # 最大30%のペナルティ
                            confidence = confidence * (1.0 - variance_penalty)
            except Exception as e:
                logger.warning(f"Failed to calculate variance penalty: {e}")
            
            return max(0.0, min(1.0, confidence))
        except Exception as e:
            logger.error(f"Failed to calculate confidence: {e}", exc_info=True)
            # エラー時は0.0を返す（フォールバック）
            return 0.0
    
    def get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """
        確信度レベルを取得
        
        Args:
            confidence: 確信度（0.0-1.0）
            
        Returns:
            確信度レベル
        """
        if confidence >= self.CONFIDENCE_THRESHOLDS[ConfidenceLevel.HIGH]:
            return ConfidenceLevel.HIGH
        elif confidence >= self.CONFIDENCE_THRESHOLDS[ConfidenceLevel.MEDIUM]:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def should_ask_question(
        self,
        analysis_result: Dict[str, Any]
    ) -> bool:
        """
        質問として投げるべきか判断
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            質問として投げるべき場合True
        """
        confidence = self.calculate_confidence(analysis_result)
        confidence_level = self.get_confidence_level(confidence)
        
        # 低確信度の場合は質問として投げる
        return confidence_level == ConfidenceLevel.LOW
    
    def generate_question(
        self,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        質問を生成
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            質問データ
        """
        findings = analysis_result.get("findings", [])
        confidence = self.calculate_confidence(analysis_result)
        
        if not findings:
            return {
                "type": "question",
                "confidence": confidence,
                "message": "構造的問題の可能性がありますが、確信度が低いです。確認をお願いします。",
                "questions": []
            }
        
        finding = findings[0]
        pattern_id = finding.get("pattern_id", "")
        evidence = finding.get("evidence", [])
        
        # パターンに基づく質問を生成
        questions = []
        
        if pattern_id == "B1_正当化フェーズ":
            questions.append("KPI下方修正が続いていますが、戦略変更の議論は行われていますか？")
            questions.append("撤退やピボットの選択肢は検討されていますか？")
        elif pattern_id == "ES1_報告遅延":
            questions.append("リスクが認識されていますが、経営層への報告は行われていますか？")
            questions.append("エスカレーションが必要な状況ですか？")
        else:
            questions.append("構造的問題の可能性がありますが、確認をお願いします。")
        
        # 証拠に基づく質問
        if evidence:
            questions.append(f"以下の証拠について確認をお願いします: {', '.join(evidence[:3])}")
        
        return {
            "type": "question",
            "confidence": confidence,
            "confidence_level": self.get_confidence_level(confidence).value,
            "message": "構造的問題の可能性がありますが、確信度が低いです。以下の点について確認をお願いします:",
            "questions": questions,
            "pattern_id": pattern_id,
            "target_roles": ["Manager", "Staff"]  # Executiveには送信しない
        }
    
    def _calculate_variance(self, values: List[float]) -> float:
        """
        分散を計算
        
        Args:
            values: 値のリスト
            
        Returns:
            分散
        """
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
