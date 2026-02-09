"""
Googleサービス統合（モック）の動作確認スクリプト

使用方法:
    # 依存関係のインストール（初回のみ）
    pip install -r requirements_minimal.txt
    
    # テストスクリプトの実行
    python test_mock_services.py

注意: バックエンドサーバーが起動している必要があります
      (uvicorn main:app --reload --host 0.0.0.0 --port 8000)
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_google_meet():
    """Google Meetサービスのテスト"""
    print("\n=== Google Meetサービス（議事録取得）===")
    response = requests.post(
        f"{BASE_URL}/api/meetings/ingest",
        json={
            "meeting_id": "test_meeting_001",
            "metadata": {
                "meeting_name": "テスト会議",
                "date": "2025-01-20",
                "participants": ["CFO", "CEO"]
            }
        }
    )
    print(f"ステータスコード: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功: 議事録が取得されました")
        print(f"   - 発言数: {data.get('parsed', {}).get('total_statements', 0)}")
        print(f"   - KPI検出: {len(data.get('parsed', {}).get('kpi_mentions', []))}件")
        print(f"   - 撤退議論: {data.get('parsed', {}).get('exit_discussed', False)}")
        return True
    else:
        print(f"❌ エラー: {response.text}")
        return False

def test_google_chat():
    """Google Chatサービスのテスト"""
    print("\n=== Google Chatサービス（チャット取得）===")
    response = requests.post(
        f"{BASE_URL}/api/chat/ingest",
        json={
            "chat_id": "test_chat_001",
            "metadata": {
                "channel_name": "テストチャンネル",
                "project_id": "test_project"
            }
        }
    )
    print(f"ステータスコード: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功: チャットが取得されました")
        print(f"   - メッセージ数: {data.get('parsed', {}).get('total_messages', 0)}")
        print(f"   - リスクメッセージ: {len(data.get('parsed', {}).get('risk_messages', []))}件")
        print(f"   - 反対意見: {len(data.get('parsed', {}).get('opposition_messages', []))}件")
        return True
    else:
        print(f"❌ エラー: {response.text}")
        return False

def test_google_workspace():
    """Google Workspaceサービスのテスト（実行フロー経由）"""
    print("\n=== Google Workspaceサービス（リサーチ・分析・資料作成）===")
    
    # 1. 議事録とチャットを取り込む
    requests.post(
        f"{BASE_URL}/api/meetings/ingest",
        json={
            "meeting_id": "test_meeting_workspace",
            "metadata": {"meeting_name": "テスト", "date": "2025-01-20", "participants": []}
        }
    )
    requests.post(
        f"{BASE_URL}/api/chat/ingest",
        json={
            "chat_id": "test_chat_workspace",
            "metadata": {"channel_name": "テスト", "project_id": "test"}
        }
    )
    
    # 2. 分析を実行
    analyze_response = requests.post(
        f"{BASE_URL}/api/analyze",
        json={
            "meeting_id": "test_meeting_workspace",
            "chat_id": "test_chat_workspace"
        }
    )
    if analyze_response.status_code != 200:
        print(f"❌ 分析エラー: {analyze_response.text}")
        return False
    
    analysis_id = analyze_response.json().get("analysis_id")
    
    # 3. エスカレーション
    escalate_response = requests.post(
        f"{BASE_URL}/api/escalate",
        json={"analysis_id": analysis_id}
    )
    if escalate_response.status_code != 200:
        print(f"❌ エスカレーションエラー: {escalate_response.text}")
        return False
    
    escalation_id = escalate_response.json().get("escalation_id")
    
    # 4. 承認
    approve_response = requests.post(
        f"{BASE_URL}/api/approve",
        json={
            "escalation_id": escalation_id,
            "decision": "approve"
        }
    )
    if approve_response.status_code != 200:
        print(f"❌ 承認エラー: {approve_response.text}")
        return False
    
    approval_id = approve_response.json().get("approval_id")
    
    # 5. 実行開始
    execute_response = requests.post(
        f"{BASE_URL}/api/execute",
        json={"approval_id": approval_id}
    )
    if execute_response.status_code != 200:
        print(f"❌ 実行エラー: {execute_response.text}")
        return False
    
    execution_id = execute_response.json().get("execution_id")
    print(f"✅ 実行開始: {execution_id}")
    
    # 6. 実行完了を待つ（最大10秒）
    for i in range(5):
        time.sleep(2)
        exec_response = requests.get(f"{BASE_URL}/api/execution/{execution_id}")
        if exec_response.status_code == 200:
            exec_data = exec_response.json()
            progress = exec_data.get("progress", 0)
            status = exec_data.get("status", "running")
            print(f"   進捗: {progress}% ({status})")
            if status == "completed":
                break
    
    # 7. 実行結果を取得
    results_response = requests.get(f"{BASE_URL}/api/execution/{execution_id}/results")
    if results_response.status_code == 200:
        results = results_response.json()
        print(f"✅ 成功: 実行結果が取得されました")
        print(f"   - 結果数: {len(results.get('results', []))}")
        for result in results.get("results", []):
            print(f"   - {result.get('name')}: {result.get('type')}")
        return True
    else:
        print(f"❌ エラー: {results_response.text}")
        return False

def test_google_drive():
    """Google Driveサービスのテスト"""
    print("\n=== Google Driveサービス（結果保存・ダウンロード）===")
    response = requests.get(f"{BASE_URL}/api/download/mock_file_id")
    print(f"ステータスコード: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功: ダウンロードURLが取得されました")
        print(f"   - ファイル名: {data.get('filename')}")
        print(f"   - ダウンロードURL: {data.get('download_url')}")
        return True
    else:
        print(f"❌ エラー: {response.text}")
        return False

def main():
    print("=" * 60)
    print("Googleサービス統合（モック）の動作確認")
    print("=" * 60)
    print("\n注意: バックエンドサーバーが起動していることを確認してください")
    print("      (uvicorn main:app --reload --host 0.0.0.0 --port 8000)")
    print("\n依存関係が不足している場合は以下を実行してください:")
    print("      pip install -r requirements_minimal.txt")
    
    results = []
    
    try:
        results.append(("Google Meet", test_google_meet()))
        results.append(("Google Chat", test_google_chat()))
        results.append(("Google Workspace", test_google_workspace()))
        results.append(("Google Drive", test_google_drive()))
    except requests.exceptions.ConnectionError:
        print("\n❌ エラー: バックエンドサーバーに接続できません")
        print("   バックエンドサーバーが起動しているか確認してください")
        return
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        return
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 すべてのテストが成功しました！")
    else:
        print("\n⚠️  一部のテストが失敗しました")

if __name__ == "__main__":
    main()

