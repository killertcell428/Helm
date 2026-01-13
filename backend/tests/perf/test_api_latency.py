"""
主要APIのレイテンシをざっくり計測する軽量パフォーマンステスト。

注意:
- バックエンドサーバーが起動している必要があります。
- これは「計測用」のテストであり、しきい値を厳しくして fail させることは目的ではありません。
"""

import time
from statistics import mean

import pytest
import requests


BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def server_check():
    """サーバーが起動しているか確認"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        if response.status_code != 200:
            pytest.skip("バックエンドサーバーが起動していません")
    except requests.exceptions.RequestException:
        pytest.skip(
            "バックエンドサーバーに接続できません。"
            "サーバーを起動してください: uvicorn main:app --reload --host 0.0.0.0 --port 8000"
        )


def _measure_latency(method: str, path: str, *, json=None, iterations: int = 10):
    latencies = []
    url = f"{BASE_URL}{path}"

    for _ in range(iterations):
        start = time.perf_counter()
        resp = requests.request(method, url, json=json)
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies.append(elapsed_ms)
        # 正常系のみを対象とする（異常系は統合テストでカバー）
        assert resp.status_code < 500

    return latencies


@pytest.mark.slow
def test_api_latency_meetings_ingest(server_check):
    """meetings/ingest のレイテンシ計測"""
    payload = {
        "meeting_id": "perf_meeting_001",
        "metadata": {
            "meeting_name": "Perf Test Meeting",
            "date": "2025-01-20",
        },
    }
    latencies = _measure_latency("POST", "/api/meetings/ingest", json=payload)
    print(f"/api/meetings/ingest latency ms: min={min(latencies):.1f}, avg={mean(latencies):.1f}, max={max(latencies):.1f}")


@pytest.mark.slow
def test_api_latency_chat_ingest(server_check):
    """chat/ingest のレイテンシ計測"""
    payload = {
        "chat_id": "perf_chat_001",
        "metadata": {
            "channel_name": "Perf Test Channel",
            "project_id": "perf_project",
        },
    }
    latencies = _measure_latency("POST", "/api/chat/ingest", json=payload)
    print(f"/api/chat/ingest latency ms: min={min(latencies):.1f}, avg={mean(latencies):.1f}, max={max(latencies):.1f}")


@pytest.mark.slow
def test_api_latency_analyze(server_check):
    """analyze のレイテンシ計測（事前にモックIDを使う）"""
    payload = {
        "meeting_id": "perf_meeting_001",
        "chat_id": "perf_chat_001",
    }
    latencies = _measure_latency("POST", "/api/analyze", json=payload)
    print(f"/api/analyze latency ms: min={min(latencies):.1f}, avg={mean(latencies):.1f}, max={max(latencies):.1f}")


@pytest.mark.slow
def test_api_latency_execute(server_check):
    """execute のレイテンシ計測（事前フロー込み）"""
    # まず1回だけフローを回して approval_id を作る
    meeting_resp = requests.post(
        f"{BASE_URL}/api/meetings/ingest",
        json={
            "meeting_id": "perf_meeting_exec",
            "metadata": {"meeting_name": "Perf Exec Meeting"},
        },
    )
    assert meeting_resp.status_code == 200

    analyze_resp = requests.post(
        f"{BASE_URL}/api/analyze",
        json={"meeting_id": "perf_meeting_exec"},
    )
    assert analyze_resp.status_code == 200
    analysis_id = analyze_resp.json()["analysis_id"]

    escalate_resp = requests.post(
        f"{BASE_URL}/api/escalate",
        json={"analysis_id": analysis_id},
    )
    if escalate_resp.status_code != 200:
        pytest.skip("エスカレーション条件を満たさず、execute フローを実行できませんでした")

    escalation_id = escalate_resp.json()["escalation_id"]

    approve_resp = requests.post(
        f"{BASE_URL}/api/approve",
        json={"escalation_id": escalation_id, "decision": "approve"},
    )
    assert approve_resp.status_code == 200
    approval_id = approve_resp.json()["approval_id"]

    latencies = _measure_latency("POST", "/api/execute", json={"approval_id": approval_id})
    print(f"/api/execute latency ms: min={min(latencies):.1f}, avg={mean(latencies):.1f}, max={max(latencies):.1f}")

