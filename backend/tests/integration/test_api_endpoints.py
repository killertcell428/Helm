"""
APIエンドポイントの統合テスト

注意: バックエンドサーバーが起動している必要があります
      uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import pytest
import requests
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def server_check():
    """サーバーが起動しているか確認"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        if response.status_code != 200:
            pytest.skip("バックエンドサーバーが起動していません")
    except requests.exceptions.RequestException:
        pytest.skip("バックエンドサーバーに接続できません。サーバーを起動してください: uvicorn main:app --reload --host 0.0.0.0 --port 8000")


class TestMeetingIngest:
    """議事録取り込みAPIのテスト"""
    
    def test_ingest_meeting(self, server_check):
        """議事録取り込みのテスト"""
        response = requests.post(
            f"{BASE_URL}/api/meetings/ingest",
            json={
                "meeting_id": "test_meeting_api_001",
                "metadata": {
                    "meeting_name": "テスト会議",
                    "date": "2025-01-20",
                    "participants": ["CFO", "CEO"]
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "meeting_id" in data
        assert "status" in data
        assert data["status"] == "success"
        assert "parsed" in data
    
    def test_ingest_meeting_with_transcript(self, server_check):
        """トランスクリプト付き議事録取り込みのテスト"""
        response = requests.post(
            f"{BASE_URL}/api/meetings/ingest",
            json={
                "meeting_id": "test_meeting_api_002",
                "transcript": "CFO: 今期の成長率は計画を下回っています。",
                "metadata": {
                    "meeting_name": "テスト会議2",
                    "date": "2025-01-20",
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestChatIngest:
    """チャット取り込みAPIのテスト"""
    
    def test_ingest_chat(self, server_check):
        """チャット取り込みのテスト"""
        response = requests.post(
            f"{BASE_URL}/api/chat/ingest",
            json={
                "chat_id": "test_chat_api_001",
                "metadata": {
                    "channel_name": "テストチャンネル",
                    "project_id": "test_project"
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "chat_id" in data
        assert "status" in data
        assert data["status"] == "success"
        assert "parsed" in data


class TestAnalyze:
    """分析APIのテスト"""
    
    def test_analyze_with_meeting(self, server_check):
        """会議データのみでの分析テスト"""
        # まず議事録を取り込む
        requests.post(
            f"{BASE_URL}/api/meetings/ingest",
            json={
                "meeting_id": "test_meeting_analyze_001",
                "metadata": {
                    "meeting_name": "分析テスト会議",
                    "date": "2025-01-20",
                }
            }
        )
        
        # 分析を実行
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={
                "meeting_id": "test_meeting_analyze_001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert "findings" in data
        assert "overall_score" in data or "score" in data
        assert "severity" in data
    
    def test_analyze_with_meeting_and_chat(self, server_check):
        """会議データとチャットデータでの分析テスト"""
        # 議事録とチャットを取り込む
        requests.post(
            f"{BASE_URL}/api/meetings/ingest",
            json={
                "meeting_id": "test_meeting_analyze_002",
                "metadata": {"meeting_name": "テスト", "date": "2025-01-20"}
            }
        )
        requests.post(
            f"{BASE_URL}/api/chat/ingest",
            json={
                "chat_id": "test_chat_analyze_002",
                "metadata": {"channel_name": "テスト", "project_id": "test"}
            }
        )
        
        # 分析を実行
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={
                "meeting_id": "test_meeting_analyze_002",
                "chat_id": "test_chat_analyze_002"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
    
    def test_get_analysis(self, server_check):
        """分析結果取得のテスト"""
        # 分析を実行
        analyze_response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={
                "meeting_id": "test_meeting_analyze_003",
                "metadata": {"meeting_name": "テスト", "date": "2025-01-20"}
            }
        )
        
        if analyze_response.status_code == 200:
            analysis_id = analyze_response.json()["analysis_id"]
            
            # 分析結果を取得
            response = requests.get(f"{BASE_URL}/api/analysis/{analysis_id}")
            assert response.status_code == 200
            data = response.json()
            assert "analysis_id" in data


class TestEscalate:
    """エスカレーションAPIのテスト"""
    
    def test_escalate(self, server_check):
        """エスカレーションのテスト"""
        # 分析を実行
        requests.post(
            f"{BASE_URL}/api/meetings/ingest",
            json={
                "meeting_id": "test_meeting_escalate_001",
                "metadata": {"meeting_name": "テスト", "date": "2025-01-20"}
            }
        )
        
        analyze_response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"meeting_id": "test_meeting_escalate_001"}
        )
        
        if analyze_response.status_code == 200:
            analysis_id = analyze_response.json()["analysis_id"]
            
            # エスカレーション
            response = requests.post(
                f"{BASE_URL}/api/escalate",
                json={"analysis_id": analysis_id}
            )
            
            # エスカレーションが成功するか、条件を満たさない場合は422が返る
            assert response.status_code in [200, 422]
            if response.status_code == 200:
                data = response.json()
                assert "escalation_id" in data
                assert "target_role" in data
                assert "reason" in data


class TestApprove:
    """承認APIのテスト"""
    
    def test_approve(self, server_check):
        """承認のテスト"""
        # エスカレーションまで実行
        requests.post(
            f"{BASE_URL}/api/meetings/ingest",
            json={
                "meeting_id": "test_meeting_approve_001",
                "metadata": {"meeting_name": "テスト", "date": "2025-01-20"}
            }
        )
        
        analyze_response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"meeting_id": "test_meeting_approve_001"}
        )
        
        if analyze_response.status_code == 200:
            analysis_id = analyze_response.json()["analysis_id"]
            
            escalate_response = requests.post(
                f"{BASE_URL}/api/escalate",
                json={"analysis_id": analysis_id}
            )
            
            if escalate_response.status_code == 200:
                escalation_data = escalate_response.json()
                escalation_id = escalation_data["escalation_id"]
                stage_approver = {"pending_cfo": "role_cfo", "pending_exec": "role_exec", "pending_planning": "dept_planning"}
                approval_id = None
                for _ in range(5):
                    response = requests.post(
                        f"{BASE_URL}/api/approve",
                        json={
                            "escalation_id": escalation_id,
                            "decision": "approve",
                            "approver_role_id": stage_approver.get(escalation_data.get("current_stage_id", ""), "role_exec")
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()
                    if "approval_id" in data:
                        approval_id = data["approval_id"]
                        assert data["decision"] == "approve"
                        break
                    if data.get("status") == "rejected":
                        break
                    escalation_data = data
                assert approval_id, "approval_id が取得できませんでした"


class TestExecute:
    """実行APIのテスト"""
    
    def test_execute(self, server_check):
        """実行のテスト"""
        # 承認まで実行
        requests.post(
            f"{BASE_URL}/api/meetings/ingest",
            json={
                "meeting_id": "test_meeting_execute_001",
                "metadata": {"meeting_name": "テスト", "date": "2025-01-20"}
            }
        )
        
        analyze_response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"meeting_id": "test_meeting_execute_001"}
        )
        
        if analyze_response.status_code == 200:
            analysis_id = analyze_response.json()["analysis_id"]
            
            escalate_response = requests.post(
                f"{BASE_URL}/api/escalate",
                json={"analysis_id": analysis_id}
            )
            
            if escalate_response.status_code == 200:
                escalation_data = escalate_response.json()
                escalation_id = escalation_data["escalation_id"]
                stage_approver = {"pending_cfo": "role_cfo", "pending_exec": "role_exec", "pending_planning": "dept_planning"}
                approval_id = None
                for _ in range(5):
                    approve_response = requests.post(
                        f"{BASE_URL}/api/approve",
                        json={
                            "escalation_id": escalation_id,
                            "decision": "approve",
                            "approver_role_id": stage_approver.get(escalation_data.get("current_stage_id", ""), "role_exec")
                        }
                    )
                    if approve_response.status_code == 200:
                        ad = approve_response.json()
                        if "approval_id" in ad:
                            approval_id = ad["approval_id"]
                            break
                        if ad.get("status") == "rejected":
                            break
                        escalation_data = ad
                if approval_id:
                    # 実行開始
                    response = requests.post(
                        f"{BASE_URL}/api/execute",
                        json={"approval_id": approval_id}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "execution_id" in data
                    assert "status" in data
                    assert "tasks" in data
    
    def test_get_execution(self, server_check):
        """実行状態取得のテスト"""
        # 実行まで実行
        requests.post(
            f"{BASE_URL}/api/meetings/ingest",
            json={
                "meeting_id": "test_meeting_execute_002",
                "metadata": {"meeting_name": "テスト", "date": "2025-01-20"}
            }
        )
        
        analyze_response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"meeting_id": "test_meeting_execute_002"}
        )
        
        if analyze_response.status_code == 200:
            analysis_id = analyze_response.json()["analysis_id"]
            
            escalate_response = requests.post(
                f"{BASE_URL}/api/escalate",
                json={"analysis_id": analysis_id}
            )
            
            if escalate_response.status_code == 200:
                escalation_id = escalate_response.json()["escalation_id"]
                
                approve_response = requests.post(
                    f"{BASE_URL}/api/approve",
                    json={
                        "escalation_id": escalation_id,
                        "decision": "approve"
                    }
                )
                
                if approve_response.status_code == 200:
                    approval_id = approve_response.json()["approval_id"]
                    
                    execute_response = requests.post(
                        f"{BASE_URL}/api/execute",
                        json={"approval_id": approval_id}
                    )
                    
                    if execute_response.status_code == 200:
                        execution_id = execute_response.json()["execution_id"]
                        
                        # 実行状態を取得
                        response = requests.get(f"{BASE_URL}/api/execution/{execution_id}")
                        assert response.status_code == 200
                        data = response.json()
                        assert "execution_id" in data
                        assert "status" in data
                        assert "progress" in data


class TestErrorHandling:
    """エラーハンドリングのテスト"""
    
    def test_get_nonexistent_analysis(self, server_check):
        """存在しない分析結果取得のテスト"""
        response = requests.get(f"{BASE_URL}/api/analysis/nonexistent_id")
        assert response.status_code == 404
    
    def test_escalate_nonexistent_analysis(self, server_check):
        """存在しない分析結果のエスカレーションテスト"""
        response = requests.post(
            f"{BASE_URL}/api/escalate",
            json={"analysis_id": "nonexistent_id"}
        )
        assert response.status_code == 404
    
    def test_analyze_nonexistent_meeting(self, server_check):
        """存在しない会議データの分析テスト"""
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"meeting_id": "nonexistent_meeting"}
        )
        assert response.status_code == 404
