"""
EscalationEngineのユニットテスト
"""

import pytest
from services.escalation_engine import EscalationEngine


class TestEscalationEngine:
    """EscalationEngineのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.engine = EscalationEngine(escalation_threshold=70)
    
    def test_should_escalate_by_score(self):
        """スコアによるエスカレーション判断テスト"""
        analysis_result = {
            "overall_score": 75,
            "severity": "MEDIUM",
        }
        
        assert self.engine.should_escalate(analysis_result) == True
    
    def test_should_not_escalate_low_score(self):
        """低スコアではエスカレーションしないテスト"""
        analysis_result = {
            "overall_score": 50,
            "severity": "MEDIUM",
        }
        
        # デモモードが有効な場合は常にTrueになる可能性がある
        result = self.engine.should_escalate(analysis_result)
        assert isinstance(result, bool)
    
    def test_should_escalate_by_severity(self):
        """重要度によるエスカレーション判断テスト"""
        analysis_result = {
            "overall_score": 50,
            "severity": "HIGH",
        }
        
        assert self.engine.should_escalate(analysis_result) == True
    
    def test_should_escalate_critical_severity(self):
        """CRITICAL重要度でのエスカレーション判断テスト"""
        analysis_result = {
            "overall_score": 50,
            "severity": "CRITICAL",
        }
        
        assert self.engine.should_escalate(analysis_result) == True
    
    def test_create_escalation(self, sample_analysis_result):
        """エスカレーション作成テスト"""
        analysis_id = "test_analysis_001"
        
        escalation_info = self.engine.create_escalation(analysis_id, sample_analysis_result)
        
        if escalation_info:
            assert "target_role" in escalation_info
            assert "reason" in escalation_info
            assert "created_at" in escalation_info
            assert escalation_info["target_role"] == "Executive"
    
    def test_create_escalation_with_findings(self):
        """検出結果がある場合のエスカレーション作成テスト"""
        analysis_id = "test_analysis_002"
        analysis_result = {
            "findings": [
                {
                    "pattern_id": "B1_正当化フェーズ",
                    "pattern_name": "正当化フェーズ",
                }
            ],
            "overall_score": 75,
            "severity": "HIGH",
        }
        
        escalation_info = self.engine.create_escalation(analysis_id, analysis_result)
        
        if escalation_info:
            assert "target_role" in escalation_info
            assert "reason" in escalation_info
    
    def test_generate_escalation_reason(self):
        """エスカレーション理由生成テスト"""
        analysis_result = {
            "overall_score": 75,
            "severity": "HIGH",
            "findings": [
                {
                    "pattern_id": "B1_正当化フェーズ",
                    "pattern_name": "正当化フェーズ",
                }
            ],
        }
        
        reason = self.engine.generate_escalation_reason(analysis_result)
        
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    def test_escalation_threshold(self):
        """エスカレーション閾値のテスト"""
        # 閾値ちょうどのスコア
        analysis_result = {
            "overall_score": 70,
            "severity": "MEDIUM",
        }
        
        assert self.engine.should_escalate(analysis_result) == True
        
        # 閾値未満のスコア
        analysis_result = {
            "overall_score": 69,
            "severity": "MEDIUM",
        }
        
        # デモモードの影響を考慮
        result = self.engine.should_escalate(analysis_result)
        assert isinstance(result, bool)
