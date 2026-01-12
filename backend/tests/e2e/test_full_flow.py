"""
エンドツーエンドテスト - 完全なフローのテスト

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


class TestFullFlow:
    """完全なフローのエンドツーエンドテスト"""
    
    def test_complete_flow(self, server_check):
        """完全なフローのテスト: 議事録取り込み → 分析 → エスカレーション → 承認 → 実行 → 結果取得"""
        
        # 1. 議事録取り込み
        meeting_response = requests.post(
            f"{BASE_URL}/api/meetings/ingest",
            json={
                "meeting_id": "e2e_test_meeting_001",
                "metadata": {
                    "meeting_name": "E2Eテスト会議",
                    "date": "2025-01-20",
                    "participants": ["CFO", "CEO"]
                }
            }
        )
        assert meeting_response.status_code == 200
        meeting_data = meeting_response.json()
        assert meeting_data["status"] == "success"
        
        # 2. チャット取り込み
        chat_response = requests.post(
            f"{BASE_URL}/api/chat/ingest",
            json={
                "chat_id": "e2e_test_chat_001",
                "metadata": {
                    "channel_name": "E2Eテストチャンネル",
                    "project_id": "e2e_test_project"
                }
            }
        )
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert chat_data["status"] == "success"
        
        # 3. 構造的問題検知
        analyze_response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={
                "meeting_id": "e2e_test_meeting_001",
                "chat_id": "e2e_test_chat_001"
            }
        )
        assert analyze_response.status_code == 200
        analysis_data = analyze_response.json()
        assert "analysis_id" in analysis_data
        assert "findings" in analysis_data
        assert "overall_score" in analysis_data or "score" in analysis_data
        
        analysis_id = analysis_data["analysis_id"]
        
        # 4. エスカレーション
        escalate_response = requests.post(
            f"{BASE_URL}/api/escalate",
            json={"analysis_id": analysis_id}
        )
        
        # エスカレーションが成功するか、条件を満たさない場合は422が返る
        if escalate_response.status_code == 200:
            escalation_data = escalate_response.json()
            assert "escalation_id" in escalation_data
            assert "target_role" in escalation_data
            
            escalation_id = escalation_data["escalation_id"]
            
            # 5. Executive承認
            approve_response = requests.post(
                f"{BASE_URL}/api/approve",
                json={
                    "escalation_id": escalation_id,
                    "decision": "approve"
                }
            )
            assert approve_response.status_code == 200
            approval_data = approve_response.json()
            assert "approval_id" in approval_data
            assert approval_data["decision"] == "approve"
            
            approval_id = approval_data["approval_id"]
            
            # 6. AI自律実行開始
            execute_response = requests.post(
                f"{BASE_URL}/api/execute",
                json={"approval_id": approval_id}
            )
            assert execute_response.status_code == 200
            execution_data = execute_response.json()
            assert "execution_id" in execution_data
            assert "status" in execution_data
            assert execution_data["status"] == "running"
            assert "tasks" in execution_data
            
            execution_id = execution_data["execution_id"]
            
            # 7. 実行状態の確認（最大10秒待機）
            max_wait = 10
            wait_interval = 2
            for _ in range(max_wait // wait_interval):
                time.sleep(wait_interval)
                exec_status_response = requests.get(f"{BASE_URL}/api/execution/{execution_id}")
                assert exec_status_response.status_code == 200
                exec_status = exec_status_response.json()
                
                if exec_status.get("status") == "completed":
                    break
            
            # 8. 実行結果取得
            results_response = requests.get(f"{BASE_URL}/api/execution/{execution_id}/results")
            assert results_response.status_code == 200
            results_data = results_response.json()
            assert "execution_id" in results_data
            assert "results" in results_data
            assert isinstance(results_data["results"], list)
        else:
            # エスカレーション条件を満たさない場合でも、フローは正常に動作していることを確認
            assert escalate_response.status_code == 422
    
    def test_flow_with_meeting_only(self, server_check):
        """会議データのみでのフローテスト"""
        
        # 1. 議事録取り込み
        meeting_response = requests.post(
            f"{BASE_URL}/api/meetings/ingest",
            json={
                "meeting_id": "e2e_test_meeting_002",
                "metadata": {
                    "meeting_name": "E2Eテスト会議2",
                    "date": "2025-01-20",
                }
            }
        )
        assert meeting_response.status_code == 200
        
        # 2. 分析（チャットなし）
        analyze_response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"meeting_id": "e2e_test_meeting_002"}
        )
        assert analyze_response.status_code == 200
        analysis_data = analyze_response.json()
        assert "analysis_id" in analysis_data
    
    def test_error_recovery(self, server_check):
        """エラー回復のテスト"""
        
        # 存在しない会議データで分析を試みる
        analyze_response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"meeting_id": "nonexistent_meeting_e2e"}
        )
        assert analyze_response.status_code == 404
        
        # エラーレスポンスに適切な情報が含まれていることを確認
        error_data = analyze_response.json()
        assert "error_id" in error_data or "message" in error_data
