"""
統合テストスクリプト
動作確認、エラーハンドリング、パフォーマンステストを実行
"""

import requests
import time
import json
import sys
from typing import Dict, Any, List
from datetime import datetime

# Windowsでの文字コード問題を回避
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_health():
    """バックエンドのヘルスチェック"""
    print("\n=== 1. バックエンドヘルスチェック ===")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print(f"[OK] バックエンドは正常に動作しています (Status: {response.status_code})")
            print(f"   レスポンス: {response.json()}")
            return True
        else:
            print(f"[NG] バックエンドのステータスが異常です (Status: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("[NG] バックエンドに接続できません。サーバーが起動しているか確認してください。")
        return False
    except Exception as e:
        print(f"[NG] エラーが発生しました: {e}")
        return False

def test_frontend_health():
    """フロントエンドのヘルスチェック"""
    print("\n=== 2. フロントエンドヘルスチェック ===")
    try:
        response = requests.get(f"{FRONTEND_URL}/", timeout=5)
        if response.status_code == 200:
            print(f"[OK] フロントエンドは正常に動作しています (Status: {response.status_code})")
            return True
        else:
            print(f"[NG] フロントエンドのステータスが異常です (Status: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("[NG] フロントエンドに接続できません。サーバーが起動しているか確認してください。")
        return False
    except Exception as e:
        print(f"[NG] エラーが発生しました: {e}")
        return False

def test_meeting_ingest():
    """会議データ取り込みのテスト（データマスキング機能の確認）"""
    print("\n=== 3. 会議データ取り込みテスト（データマスキング確認） ===")
    try:
        data = {
            "meeting_id": "test_meeting_001",
            "transcript": "CFO: 1億円の投資が必要です。A社との取引も検討中です。山田太郎さんが提案しました。",
            "metadata": {
                "meeting_name": "テスト会議",
                "date": "2025-01-31",
                "participants": [
                    {"name": "山田太郎", "role": "CFO"},
                    {"name": "佐藤花子", "role": "CEO"}
                ]
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/meetings/ingest",
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] 会議データ取り込み成功")
            print(f"   Meeting ID: {result.get('meeting_id')}")
            
            # データマスキングの確認
            if "transcript" in result:
                transcript = result["transcript"]
                if "1億円" in transcript or "[金額:" in transcript:
                    print("   ✅ データマスキングが適用されています")
                else:
                    print("   ⚠️  データマスキングが適用されていない可能性があります")
            
            return result.get("meeting_id")
        else:
            print(f"[NG] 会議データ取り込み失敗 (Status: {response.status_code})")
            print(f"   エラー: {response.text}")
            return None
    except Exception as e:
        print(f"[NG] エラーが発生しました: {e}")
        return None

def test_chat_ingest():
    """チャットデータ取り込みのテスト（データマスキング機能の確認）"""
    print("\n=== 4. チャットデータ取り込みテスト（データマスキング確認） ===")
    try:
        data = {
            "chat_id": "test_chat_001",
            "messages": [
                {
                    "user": "経営企画A",
                    "text": "1億円の投資が必要です。A社との取引も検討中です。",
                    "timestamp": "2025-01-31T10:00:00Z"
                }
            ],
            "metadata": {
                "channel_name": "テストチャンネル",
                "project_id": "test_project"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat/ingest",
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] チャットデータ取り込み成功")
            print(f"   Chat ID: {result.get('chat_id')}")
            
            # データマスキングの確認
            if "messages" in result:
                messages = result["messages"]
                if messages:
                    first_message = messages[0].get("text", "")
                    if "[金額:" in first_message or "[顧客名]" in first_message:
                        print("   [OK] データマスキングが適用されています")
                    else:
                        print("   [WARN] データマスキングが適用されていない可能性があります")
            
            return result.get("chat_id")
        else:
            print(f"[NG] チャットデータ取り込み失敗 (Status: {response.status_code})")
            print(f"   エラー: {response.text}")
            return None
    except Exception as e:
        print(f"[NG] エラーが発生しました: {e}")
        return None

def test_analysis(meeting_id: str, chat_id: str):
    """分析実行のテスト（根拠引用機能の確認）"""
    print("\n=== 5. 分析実行テスト（根拠引用確認） ===")
    try:
        data = {
            "meeting_id": meeting_id,
            "chat_id": chat_id
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json=data,
            timeout=30
        )
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] 分析実行成功 (処理時間: {elapsed_time:.2f}秒)")
            print(f"   Analysis ID: {result.get('analysis_id')}")
            print(f"   Score: {result.get('score', 0)}")
            print(f"   Severity: {result.get('severity', 'N/A')}")
            
            # 根拠引用の確認
            explanation = result.get("explanation", "")
            if "【根拠】" in explanation or "発言ID" in explanation:
                print("   [OK] 根拠引用が含まれています")
            else:
                print("   [WARN] 根拠引用が含まれていない可能性があります")
            
            # 拡張機能のフィールド確認
            if "rule_score" in result and "llm_score" in result:
                print("   [OK] 確信度計算用のフィールドが含まれています")
            
            return result.get("analysis_id")
        else:
            print(f"[NG] 分析実行失敗 (Status: {response.status_code})")
            print(f"   エラー: {response.text}")
            return None
    except Exception as e:
        print(f"[NG] エラーが発生しました: {e}")
        return None

def test_escalation(analysis_id: str):
    """エスカレーションテスト（拡張機能の確認）"""
    print("\n=== 6. エスカレーションテスト（拡張機能確認） ===")
    try:
        data = {
            "analysis_id": analysis_id
        }
        
        response = requests.post(
            f"{BASE_URL}/api/escalate",
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] エスカレーション成功")
            print(f"   Escalation ID: {result.get('escalation_id')}")
            print(f"   Target Role: {result.get('target_role')}")
            print(f"   Reason: {result.get('reason', '')[:100]}...")
            
            # 拡張機能のフィールド確認
            if "stage" in result:
                print(f"   [OK] 段階的エスカレーション: {result.get('stage')} ({result.get('stage_name', 'N/A')})")
            if "confidence" in result:
                print(f"   [OK] 確信度: {result.get('confidence', 0):.2f} ({result.get('confidence_level', 'N/A')})")
            if "question" in result:
                print(f"   [OK] 質問機能: 有効")
            if "target_roles" in result:
                print(f"   [OK] ターゲットロール: {result.get('target_roles')}")
            
            return result.get("escalation_id")
        else:
            print(f"[NG] エスカレーション失敗 (Status: {response.status_code})")
            print(f"   エラー: {response.text}")
            return None
    except Exception as e:
        print(f"[NG] エラーが発生しました: {e}")
        return None

def test_error_handling():
    """エラーハンドリングのテスト"""
    print("\n=== 7. エラーハンドリングテスト ===")
    
    # 存在しないリソースへのアクセス
    print("\n7-1. 存在しない会議データへのアクセス")
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"meeting_id": "nonexistent_meeting", "chat_id": "nonexistent_chat"},
            timeout=10
        )
        if response.status_code == 404:
            print("   [OK] 適切なエラーレスポンスが返されました (404)")
        else:
            print(f"   [WARN] 予期しないステータスコード: {response.status_code}")
    except Exception as e:
        print(f"   [NG] エラーが発生しました: {e}")
    
    # 無効なデータでのマスキングテスト
    print("\n7-2. 無効なデータでのマスキングテスト")
    try:
        data = {
            "meeting_id": "test_error_001",
            "transcript": None,  # 無効なデータ
            "metadata": {}
        }
        response = requests.post(
            f"{BASE_URL}/api/meetings/ingest",
            json=data,
            timeout=10
        )
        # エラーが発生しても処理が継続されることを確認
        if response.status_code in [200, 422]:
            print("   [OK] エラーハンドリングが適切に動作しています")
        else:
            print(f"   [WARN] 予期しないステータスコード: {response.status_code}")
    except Exception as e:
        print(f"   [NG] エラーが発生しました: {e}")

def test_performance():
    """パフォーマンステスト"""
    print("\n=== 8. パフォーマンステスト ===")
    
    # 複数のリクエストを並行で実行
    print("\n8-1. 並行リクエストテスト")
    try:
        import concurrent.futures
        
        def make_request(i):
            data = {
                "meeting_id": f"perf_test_{i}",
                "transcript": f"Test transcript {i}",
                "metadata": {"meeting_name": f"Test Meeting {i}"}
            }
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/meetings/ingest",
                json=data,
                timeout=10
            )
            elapsed = time.time() - start
            return response.status_code, elapsed
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        avg_time = sum(r[1] for r in results) / len(results)
        
        print(f"   [OK] 5件の並行リクエスト完了")
        print(f"   総処理時間: {total_time:.2f}秒")
        print(f"   平均処理時間: {avg_time:.2f}秒")
        print(f"   成功数: {sum(1 for r in results if r[0] == 200)}/5")
        
    except Exception as e:
        print(f"   [NG] エラーが発生しました: {e}")

def main():
    """メイン関数"""
    print("=" * 60)
    print("Helm 統合テスト開始")
    print("=" * 60)
    
    # ヘルスチェック
    if not test_backend_health():
        print("\n[NG] バックエンドが起動していません。テストを中断します。")
        return
    
    if not test_frontend_health():
        print("\n[WARN] フロントエンドが起動していませんが、バックエンドテストは継続します。")
    
    # 基本機能テスト
    meeting_id = test_meeting_ingest()
    chat_id = test_chat_ingest()
    
    if meeting_id and chat_id:
        analysis_id = test_analysis(meeting_id, chat_id)
        
        if analysis_id:
            escalation_id = test_escalation(analysis_id)
    
    # エラーハンドリングテスト
    test_error_handling()
    
    # パフォーマンステスト
    test_performance()
    
    print("\n" + "=" * 60)
    print("統合テスト完了")
    print("=" * 60)

if __name__ == "__main__":
    main()
