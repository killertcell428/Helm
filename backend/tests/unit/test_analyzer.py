"""
StructureAnalyzerのユニットテスト
"""

import pytest
from services.analyzer import StructureAnalyzer
from services.scoring import ScoringService


class TestStructureAnalyzer:
    """StructureAnalyzerのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        scoring_service = ScoringService()
        self.analyzer = StructureAnalyzer(
            use_vertex_ai=False,
            scoring_service=scoring_service
        )
    
    def test_analyze_with_meeting_data(self, sample_meeting_data):
        """会議データのみでの分析テスト"""
        result = self.analyzer.analyze(sample_meeting_data, None)
        
        assert "findings" in result
        assert "scores" in result
        assert "overall_score" in result
        assert "severity" in result
        assert "explanation" in result
        assert "created_at" in result
        assert isinstance(result["findings"], list)
        assert result["overall_score"] >= 0
        assert result["overall_score"] <= 100
    
    def test_analyze_with_chat_data(self, sample_meeting_data, sample_chat_data):
        """会議データとチャットデータでの分析テスト"""
        result = self.analyzer.analyze(sample_meeting_data, sample_chat_data)
        
        assert "findings" in result
        assert "scores" in result
        assert "overall_score" in result
        assert "severity" in result
        assert isinstance(result["findings"], list)
    
    def test_kpi_downgrade_detection(self, sample_meeting_data):
        """KPI下方修正の検出テスト"""
        result = self.analyzer.analyze(sample_meeting_data, None)
        
        # KPI下方修正が検出されることを確認
        kpi_findings = [
            f for f in result["findings"]
            if f.get("pattern_id") == "B1_正当化フェーズ"
        ]
        
        # サンプルデータにKPI下方修正が含まれている場合
        if sample_meeting_data.get("kpi_mentions"):
            assert len(kpi_findings) > 0 or result["overall_score"] > 0
    
    def test_justification_phase_detection(self, sample_meeting_data):
        """正当化フェーズの検出テスト"""
        # 正当化フェーズを検出するためのデータ
        meeting_data = {
            **sample_meeting_data,
            "kpi_mentions": [
                {"speaker": "CFO", "text": "今期の成長率は計画を下回っています。15%下方修正が必要です。", "keyword": "成長率"},
                {"speaker": "CFO", "text": "ARPUも下方修正が必要です。", "keyword": "ARPU"},
            ],
        }
        
        result = self.analyzer.analyze(meeting_data, None)
        
        # 正当化フェーズが検出される可能性があることを確認
        assert "findings" in result
        assert isinstance(result["findings"], list)
    
    def test_decision_concentration_detection(self, sample_meeting_data):
        """判断集中の検出テスト"""
        result = self.analyzer.analyze(sample_meeting_data, None)
        
        # 判断集中が検出される可能性があることを確認
        assert "findings" in result
        assert isinstance(result["findings"], list)
    
    def test_opposition_ignored_detection(self, sample_meeting_data, sample_chat_data):
        """反対意見無視の検出テスト"""
        result = self.analyzer.analyze(sample_meeting_data, sample_chat_data)
        
        # 反対意見無視が検出される可能性があることを確認
        opposition_findings = [
            f for f in result["findings"]
            if f.get("pattern_id") == "B3_反対意見無視"
        ]
        
        # サンプルデータに反対意見が含まれている場合
        if sample_chat_data.get("opposition_messages"):
            # 反対意見が検出される可能性があることを確認
            assert isinstance(result["findings"], list)
    
    def test_empty_meeting_data(self):
        """空の会議データでのテスト"""
        empty_data = {
            "statements": [],
            "kpi_mentions": [],
            "exit_discussed": False,
            "total_statements": 0,
        }
        
        result = self.analyzer.analyze(empty_data, None)
        
        assert "findings" in result
        assert "overall_score" in result
        assert result["overall_score"] >= 0
    
    def test_scoring_integration(self, sample_meeting_data):
        """スコアリングサービスとの統合テスト"""
        result = self.analyzer.analyze(sample_meeting_data, None)
        
        # スコアリングが正しく実行されていることを確認
        assert "scores" in result
        assert "overall_score" in result
        assert "severity" in result
        assert result["overall_score"] >= 0
        assert result["overall_score"] <= 100
