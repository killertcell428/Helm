"""
WebSocketの応答時間（progress/ completed）をざっくり計測するテスト。

注意:
- バックエンドサーバーが起動している必要があります。
- `websockets` パッケージが必要です。
"""

import time
from typing import Tuple

import pytest
import requests

from tests.e2e.utils_websocket import collect_execution_messages


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


def _prepare_execution() -> str:
    """
    WebSocket計測用の execution_id を1つ作成する簡易フロー。

    Returns:
        execution_id
    """
    meeting_resp = requests.post(
        f"{BASE_URL}/api/meetings/ingest",
        json={
            "meeting_id": "perf_ws_meeting",
            "metadata": {"meeting_name": "Perf WS Meeting"},
        },
    )
    assert meeting_resp.status_code == 200

    analyze_resp = requests.post(
        f"{BASE_URL}/api/analyze",
        json={"meeting_id": "perf_ws_meeting"},
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

    execute_resp = requests.post(
        f"{BASE_URL}/api/execute",
        json={"approval_id": approval_id},
    )
    assert execute_resp.status_code == 200
    execution_id = execute_resp.json()["execution_id"]
    return execution_id


@pytest.mark.slow
@pytest.mark.websocket
def test_websocket_latency_progress_and_completed(server_check):
    """
    WebSocket接続〜progress/ completed までのおおよその時間を計測する。

    - execute 呼び出しから completed までの時間
    - WebSocket 接続から最初の progress までの時間
    """
    # execution を準備
    t0 = time.perf_counter()
    execution_id = _prepare_execution()

    # WebSocketでメッセージを収集しつつ時間を計測
    t1 = time.perf_counter()
    progress_messages, completed_messages = collect_execution_messages(execution_id, timeout_seconds=30)
    t2 = time.perf_counter()

    # 少なくとも1つはprogressが存在すること
    assert len(progress_messages) > 0
    assert len(completed_messages) > 0

    # メトリクス出力（fail条件は設けず、現状把握のみ）
    exec_total_ms = (t2 - t0) * 1000
    ws_duration_ms = (t2 - t1) * 1000

    print(
        f"WebSocket latency: total_exec_ms={exec_total_ms:.1f}, "
        f"ws_session_ms={ws_duration_ms:.1f}, "
        f"progress_count={len(progress_messages)}, completed_count={len(completed_messages)}"
    )

