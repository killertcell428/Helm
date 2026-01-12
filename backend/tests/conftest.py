"""
pytest設定ファイル
共通のフィクスチャと設定
"""

import pytest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

@pytest.fixture
def sample_meeting_data():
    """サンプル会議データ"""
    return {
        "statements": [
            {"speaker": "CFO", "text": "今期の成長率は計画を下回っています。15%下方修正が必要です。"},
            {"speaker": "CEO", "text": "了解しました。その方針で進めましょう。"},
            {"speaker": "CFO", "text": "ARPUも下方修正が必要です。"},
            {"speaker": "CEO", "text": "承認します。"},
        ],
        "kpi_mentions": [
            {"speaker": "CFO", "text": "今期の成長率は計画を下回っています。15%下方修正が必要です。", "keyword": "成長率"},
            {"speaker": "CFO", "text": "ARPUも下方修正が必要です。", "keyword": "ARPU"},
        ],
        "exit_discussed": False,
        "total_statements": 4,
    }

@pytest.fixture
def sample_chat_data():
    """サンプルチャットデータ"""
    return {
        "messages": [
            {"sender": "Member1", "text": "この方針に反対です。リスクが高すぎます。"},
            {"sender": "CFO", "text": "了解しました。進めます。"},
            {"sender": "Member2", "text": "私も反対です。"},
            {"speaker": "CFO", "text": "承認済みです。"},
        ],
        "risk_messages": [
            {"sender": "Member1", "text": "この方針に反対です。リスクが高すぎます。"},
        ],
        "opposition_messages": [
            {"sender": "Member1", "text": "この方針に反対です。リスクが高すぎます。"},
            {"sender": "Member2", "text": "私も反対です。"},
        ],
        "total_messages": 4,
    }

@pytest.fixture
def sample_analysis_result():
    """サンプル分析結果"""
    return {
        "findings": [
            {
                "pattern_id": "B1_正当化フェーズ",
                "pattern_name": "正当化フェーズ",
                "description": "KPI下方修正が繰り返し行われています",
                "quantitative_scores": {
                    "kpi_downgrade_count": 2,
                    "justification_ratio": 0.5,
                },
            }
        ],
        "scores": {
            "importance": 75,
            "urgency": 60,
        },
        "overall_score": 70,
        "severity": "HIGH",
        "urgency": "HIGH",
        "explanation": "KPI下方修正が2回検出されました。",
        "created_at": "2025-01-20T10:00:00",
    }
