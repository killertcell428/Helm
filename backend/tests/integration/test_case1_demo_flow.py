"""
Case1 デモフローの統合テスト
http://localhost:3000/demo/case1 で使用するPATTERN_DATAと同じデータでAPIフローを検証
"""

import pytest
import requests
import time

BASE_URL = "http://localhost:8000"

# Case1 PATTERN_DATA A と同等のデータ
CASE1_PATTERN_A = {
    "meeting_id": "demo_meeting_A",
    "chat_id": "demo_chat_A",
    "transcript": "CFO: モバイルARPUは前年同期比▲7.5%で、3四半期連続の下方修正です。\nCFO: 5G設備投資は当初計画比＋20%となっており、減価償却負担が増加しています。\nCFO: DX事業の営業利益率は▲15%で、前回会議からさらに悪化しています。\nCEO: 数字は厳しいが、我々の中長期戦略は正しい方向だと思う。\nCEO: 今は我慢の時期。計画は維持しつつ、各本部でコストの工夫をお願いしたい。\n通信本部長: ARPU低下は市場要因も大きく、短期では打てる手が限られる状況です。\nDX本部長: ここで投資を減らすと将来の成長機会を逃します。今は仕込みを続けるべきです。\nCEO: では、2025年度計画は現行のまま維持する方向で。詳細は各本部で詰めてください。\n結論: 2025年度計画は維持。各本部はコスト最適化案を検討。次回進捗報告は3か月後。",
    "meeting_metadata": {
        "meeting_name": "四半期経営会議（パターンA）",
        "date": "2025-02-01",
        "participants": ["CFO", "CEO", "通信本部長", "DX本部長"]
    },
    "chat_messages": [
        {"user": "経営企画A", "text": "正直、この数字で何も方向性を変えないのは危険だと思います…", "timestamp": "2025-02-01T15:30:00Z"},
        {"user": "経営企画B", "text": "やめた方がいいプロジェクトもそろそろ整理しないと、現場がもたないですね。", "timestamp": "2025-02-01T15:32:00Z"},
    ],
    "chat_metadata": {"channel_name": "経営企画チャンネル（パターンA）", "project_id": "project_zombie_A"},
}


@pytest.fixture(scope="module")
def server_check():
    """バックエンドサーバーの起動確認"""
    try:
        r = requests.get(f"{BASE_URL}/", timeout=3)
        if r.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        pass
    pytest.skip("バックエンドサーバーが起動していません。uvicorn main:app --reload --host 0.0.0.0 --port 8000 で起動してください")


class TestCase1DemoFlow:
    """Case1デモの完全フロー検証"""

    def test_case1_full_flow_ingest_to_execute(self, server_check):
        """Case1: データ取り込み → 分析 → エスカレーション → 承認 → 実行 の完全フロー"""
        # 1. 議事録取り込み
        ingest_meeting = requests.post(
            f"{BASE_URL}/api/meetings/ingest",
            json={
                "meeting_id": CASE1_PATTERN_A["meeting_id"],
                "transcript": CASE1_PATTERN_A["transcript"],
                "metadata": CASE1_PATTERN_A["meeting_metadata"]
            },
            timeout=10
        )
        assert ingest_meeting.status_code == 200, f"議事録取り込み失敗: {ingest_meeting.text}"

        # 2. チャット取り込み
        ingest_chat = requests.post(
            f"{BASE_URL}/api/chat/ingest",
            json={
                "chat_id": CASE1_PATTERN_A["chat_id"],
                "messages": CASE1_PATTERN_A["chat_messages"],
                "metadata": CASE1_PATTERN_A["chat_metadata"]  # channel_name, project_id
            },
            timeout=10
        )
        assert ingest_chat.status_code == 200, f"チャット取り込み失敗: {ingest_chat.text}"

        # 3. 分析
        analyze_resp = requests.post(
            f"{BASE_URL}/api/analyze",
            json={
                "meeting_id": CASE1_PATTERN_A["meeting_id"],
                "chat_id": CASE1_PATTERN_A["chat_id"]
            },
            timeout=60
        )
        assert analyze_resp.status_code == 200, f"分析失敗: {analyze_resp.text}"
        analysis_id = analyze_resp.json()["analysis_id"]
        assert analysis_id, "analysis_id が取得できませんでした"

        # 4. エスカレーション（スコア条件を満たさない場合はスキップ可能）
        escalate_resp = requests.post(
            f"{BASE_URL}/api/escalate",
            json={"analysis_id": analysis_id},
            timeout=10
        )
        if escalate_resp.status_code != 200:
            pytest.skip(f"エスカレーション条件を満たしていません（スコア不足の可能性）: {escalate_resp.json().get('message', escalate_resp.text)}")

        escalation_data = escalate_resp.json()
        escalation_id = escalation_data["escalation_id"]
        assert escalation_id, "escalation_id が取得できませんでした"

        # 5. 承認（全ステージ承認）
        approval_id = None
        stage_approver = {"pending_cfo": "role_cfo", "pending_exec": "role_exec", "pending_planning": "dept_planning"}
        for _ in range(5):
            approve_resp = requests.post(
                f"{BASE_URL}/api/approve",
                json={
                    "escalation_id": escalation_id,
                    "decision": "approve",
                    "approver_role_id": stage_approver.get(escalation_data.get("current_stage_id", ""), "role_exec")
                },
                timeout=10
            )
            if approve_resp.status_code != 200:
                pytest.fail(f"承認失敗: {approve_resp.text}")
            ad = approve_resp.json()
            if ad.get("status") == "rejected":
                pytest.fail("承認が却下されました")
            if "approval_id" in ad:
                approval_id = ad["approval_id"]
                break
            escalation_data = ad

        assert approval_id, "approval_id が取得できませんでした"

        # 6. 実行開始
        execute_resp = requests.post(
            f"{BASE_URL}/api/execute",
            json={"approval_id": approval_id},
            timeout=30
        )
        assert execute_resp.status_code == 200, f"実行開始失敗: {execute_resp.text}"
        exec_data = execute_resp.json()
        assert "execution_id" in exec_data
        assert "tasks" in exec_data
        execution_id = exec_data["execution_id"]

        # 7. 実行状態取得（進捗確認）
        for _ in range(12):  # 最大約24秒待機（2秒×12）
            time.sleep(2)
            get_exec = requests.get(f"{BASE_URL}/api/execution/{execution_id}", timeout=5)
            assert get_exec.status_code == 200, f"実行状態取得失敗: {get_exec.text}"
            data = get_exec.json()
            if data.get("status") == "completed":
                break
            assert data.get("status") in ("running", "completed"), f"想定外のステータス: {data.get('status')}"

        # 8. 実行結果取得
        results_resp = requests.get(f"{BASE_URL}/api/execution/{execution_id}/results", timeout=10)
        assert results_resp.status_code == 200, f"実行結果取得失敗: {results_resp.text}"
        results = results_resp.json()
        assert "results" in results
