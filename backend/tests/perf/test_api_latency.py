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


def _measure_latency(method: str, path: str, *, json=None, iterations: int = 10, timeout: int = 30):
    """レイテンシ計測。timeout でハングを防ぐ。"""
    latencies = []
    url = f"{BASE_URL}{path}"

    for _ in range(iterations):
        start = time.perf_counter()
        resp = requests.request(method, url, json=json, timeout=timeout)
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
def test_api_latency_root(server_check):
    """GET / のレイテンシ（Cache-Control 付き）。キャッシュヒット想定で短いことの目安。"""
    latencies = _measure_latency("GET", "/")
    print(f"GET / latency ms: min={min(latencies):.1f}, avg={mean(latencies):.1f}, max={max(latencies):.1f}")


@pytest.mark.slow
def test_api_latency_get_analysis_cache_hit(server_check):
    """GET /api/analysis/{id} のキャッシュヒット時は2回目以降が高速であることの目安。"""
    # 事前に分析を作成
    analyze_resp = requests.post(
        f"{BASE_URL}/api/analyze",
        json={"meeting_id": "perf_meeting_001", "chat_id": "perf_chat_001"},
        timeout=120,
    )
    if analyze_resp.status_code != 200:
        pytest.skip("analyze が失敗したためスキップ")
    analysis_id = analyze_resp.json()["analysis_id"]
    # 1回目（キャッシュミス）
    first = _measure_latency("GET", f"/api/analysis/{analysis_id}", iterations=1)
    # 2回目（キャッシュヒット）
    second = _measure_latency("GET", f"/api/analysis/{analysis_id}", iterations=5)
    print(
        f"GET /api/analysis cache: first={first[0]:.1f}ms, cached_avg={mean(second):.1f}ms"
    )
    # キャッシュヒット時は平均が 1 回目より短いことを期待（目安）
    assert mean(second) <= first[0] * 2, "cached response should be comparable or faster"


@pytest.mark.slow
def test_api_latency_execute(server_check):
    """execute のレイテンシ計測（事前フロー込み）。LLM を含むため反復は2回・長めの timeout。"""
    # まず1回だけフローを回して approval_id を作る
    meeting_resp = requests.post(
        f"{BASE_URL}/api/meetings/ingest",
        json={
            "meeting_id": "perf_meeting_exec",
            "metadata": {"meeting_name": "Perf Exec Meeting"},
        },
        timeout=30,
    )
    assert meeting_resp.status_code == 200

    analyze_resp = requests.post(
        f"{BASE_URL}/api/analyze",
        json={"meeting_id": "perf_meeting_exec"},
        timeout=120,
    )
    assert analyze_resp.status_code == 200
    analysis_id = analyze_resp.json()["analysis_id"]

    escalate_resp = requests.post(
        f"{BASE_URL}/api/escalate",
        json={"analysis_id": analysis_id},
        timeout=30,
    )
    if escalate_resp.status_code != 200:
        pytest.skip("エスカレーション条件を満たさず、execute フローを実行できませんでした")

    escalation_id = escalate_resp.json()["escalation_id"]

    approve_resp = requests.post(
        f"{BASE_URL}/api/approve",
        json={"escalation_id": escalation_id, "decision": "approve"},
        timeout=30,
    )
    assert approve_resp.status_code == 200
    approval_id = approve_resp.json()["approval_id"]

    # execute は LLM タスク生成を含むため重い。反復は2回・タイムアウト120秒で計測
    latencies = _measure_latency(
        "POST", "/api/execute",
        json={"approval_id": approval_id},
        iterations=2,
        timeout=120,
    )
    print(f"/api/execute latency ms: min={min(latencies):.1f}, avg={mean(latencies):.1f}, max={max(latencies):.1f}")

