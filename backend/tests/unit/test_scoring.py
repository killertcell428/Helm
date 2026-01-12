"""
ScoringServiceのユニットテスト
"""

import pytest
from services.scoring import ScoringService, SeverityLevel, UrgencyLevel


class TestScoringService:
    """ScoringServiceのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.scoring_service = ScoringService()
    
    def test_evaluate_justification_phase(self):
        """正当化フェーズの評価テスト"""
        finding = {
            "pattern_id": "B1_正当化フェーズ",
            "pattern_name": "正当化フェーズ",
            "quantitative_scores": {
                "kpi_downgrade_count": 2,
                "justification_ratio": 0.5,
            },
        }
        
        result = self.scoring_service.evaluate(finding)
        
        assert "importance_score" in result
        assert "urgency_score" in result
        assert "overall_score" in result
        assert "severity" in result
        assert "urgency" in result
        assert "explanation" in result
        assert result["overall_score"] >= 0
        assert result["overall_score"] <= 100
    
    def test_evaluate_decision_concentration(self):
        """判断集中の評価テスト"""
        finding = {
            "pattern_id": "B2_判断集中",
            "pattern_name": "判断集中",
            "quantitative_scores": {
                "decision_concentration_ratio": 0.8,
            },
        }
        
        result = self.scoring_service.evaluate(finding)
        
        assert "importance_score" in result
        assert "urgency_score" in result
        assert "overall_score" in result
        assert result["overall_score"] >= 0
        assert result["overall_score"] <= 100
    
    def test_evaluate_opposition_ignored(self):
        """反対意見無視の評価テスト"""
        finding = {
            "pattern_id": "B3_反対意見無視",
            "pattern_name": "反対意見無視",
            "quantitative_scores": {
                "opposition_ignored_count": 2,
            },
        }
        
        result = self.scoring_service.evaluate(finding)
        
        assert "importance_score" in result
        assert "urgency_score" in result
        assert "overall_score" in result
        assert result["overall_score"] >= 0
        assert result["overall_score"] <= 100
    
    def test_severity_levels(self):
        """重要度レベルのテスト"""
        # CRITICAL (90-100点)
        finding = {
            "pattern_id": "B1_正当化フェーズ",
            "quantitative_scores": {
                "kpi_downgrade_count": 5,
                "justification_ratio": 0.9,
            },
        }
        result = self.scoring_service.evaluate(finding)
        if result["overall_score"] >= 90:
            assert result["severity"] == SeverityLevel.CRITICAL
        
        # HIGH (70-89点)
        finding = {
            "pattern_id": "B1_正当化フェーズ",
            "quantitative_scores": {
                "kpi_downgrade_count": 2,
                "justification_ratio": 0.5,
            },
        }
        result = self.scoring_service.evaluate(finding)
        if 70 <= result["overall_score"] < 90:
            assert result["severity"] == SeverityLevel.HIGH
    
    def test_urgency_levels(self):
        """緊急度レベルのテスト"""
        finding = {
            "pattern_id": "B1_正当化フェーズ",
            "quantitative_scores": {
                "kpi_downgrade_count": 2,
                "justification_ratio": 0.5,
            },
        }
        
        result = self.scoring_service.evaluate(finding)
        
        assert result["urgency"] in [
            UrgencyLevel.IMMEDIATE,
            UrgencyLevel.URGENT,
            UrgencyLevel.HIGH,
            UrgencyLevel.MEDIUM,
            UrgencyLevel.LOW,
        ]
    
    def test_explanation_generation(self):
        """説明生成のテスト"""
        finding = {
            "pattern_id": "B1_正当化フェーズ",
            "pattern_name": "正当化フェーズ",
            "quantitative_scores": {
                "kpi_downgrade_count": 2,
                "justification_ratio": 0.5,
            },
        }
        
        result = self.scoring_service.evaluate(finding)
        
        assert "explanation" in result
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 0
    
    def test_unknown_pattern(self):
        """未知のパターンのテスト"""
        finding = {
            "pattern_id": "UNKNOWN_PATTERN",
            "quantitative_scores": {},
        }
        
        result = self.scoring_service.evaluate(finding)
        
        # 未知のパターンでもデフォルト値が返されることを確認
        assert "overall_score" in result
        assert result["overall_score"] >= 0
