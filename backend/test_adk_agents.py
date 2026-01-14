"""
ADKエージェントの動作確認スクリプト
実際のAPI統合（Vertex AI Search、Google Drive、Google Chat/Gmail API）がなくても動作確認可能
"""

import asyncio
import os
import sys
from typing import Dict, Any

# .envファイルを読み込む
from dotenv import load_dotenv
load_dotenv()

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.adk_setup import ADK_AVAILABLE, get_model
from services.agents.research_agent import execute_research_task, build_research_agent
from services.agents.analysis_agent import execute_analysis_task, build_analysis_agent
from services.agents.notification_agent import execute_notification_task, build_notification_agent
from services.agents.shared_context import SharedContext

def print_section(title: str):
    """セクション区切りを表示"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_adk_setup():
    """ADKのセットアップ状況を確認"""
    print_section("ADKセットアップ確認")
    
    print(f"ADK利用可能: {ADK_AVAILABLE}")
    
    if ADK_AVAILABLE:
        print("✅ ADKはインストールされています")
    else:
        print("⚠️  ADKはインストールされていません（モックモードで動作）")
    
    # APIキーの確認
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        print(f"✅ APIキーが設定されています: {api_key[:10]}...")
    else:
        print("⚠️  APIキーが設定されていません（モックモードで動作）")
    
    # モデルの確認
    model = get_model()
    if model:
        print(f"✅ LLMモデルが取得できました: {type(model).__name__}")
    else:
        print("⚠️  LLMモデルが取得できませんでした（モックモードで動作）")
    
    return ADK_AVAILABLE and model is not None

async def test_research_agent():
    """ResearchAgentの動作確認"""
    print_section("ResearchAgent テスト")
    
    task = {
        "id": "test_research_1",
        "name": "ARPU動向",
        "type": "research",
        "description": "市場データ分析：ARPU動向"
    }
    
    context = SharedContext()
    
    try:
        result = await execute_research_task(task, context.get_context())
        print(f"✅ ResearchAgent実行成功")
        print(f"   ステータス: {result.get('status')}")
        print(f"   ADK使用: {result.get('is_adk_generated', False)}")
        print(f"   トピック: {result.get('topic', 'N/A')}")
        if result.get('data'):
            data_preview = str(result.get('data'))[:100]
            print(f"   データプレビュー: {data_preview}...")
        return True
    except Exception as e:
        print(f"❌ ResearchAgent実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_analysis_agent():
    """AnalysisAgentの動作確認"""
    print_section("AnalysisAgent テスト")
    
    task = {
        "id": "test_analysis_1",
        "name": "財務シミュレーション",
        "type": "analysis",
        "description": "社内データ統合と財務シミュレーション"
    }
    
    context = SharedContext()
    
    try:
        result = await execute_analysis_task(task, context.get_context())
        print(f"✅ AnalysisAgent実行成功")
        print(f"   ステータス: {result.get('status')}")
        print(f"   ADK使用: {result.get('is_adk_generated', False)}")
        if result.get('data'):
            data_preview = str(result.get('data'))[:100]
            print(f"   データプレビュー: {data_preview}...")
        return True
    except Exception as e:
        print(f"❌ AnalysisAgent実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_notification_agent():
    """NotificationAgentの動作確認"""
    print_section("NotificationAgent テスト")
    
    task = {
        "id": "test_notification_1",
        "name": "関係部署への通知",
        "type": "notification",
        "description": "関係部署への事前通知"
    }
    
    context = SharedContext()
    # ドキュメントURLをコンテキストに追加（通知エージェントが参照）
    context._context["document_url"] = "https://docs.google.com/document/d/test123"
    
    try:
        result = await execute_notification_task(task, context.get_context())
        print(f"✅ NotificationAgent実行成功")
        print(f"   ステータス: {result.get('status')}")
        print(f"   ADK使用: {result.get('is_adk_generated', False)}")
        print(f"   受信者数: {result.get('recipients', 'N/A')}")
        print(f"   注意: {result.get('note', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ NotificationAgent実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_shared_context():
    """SharedContextの動作確認"""
    print_section("SharedContext テスト")
    
    context = SharedContext()
    
    # 結果を保存
    context.save_result("task1", {"data": "test_data_1", "status": "completed"})
    context.save_result("task2", {"document_id": "doc123", "view_url": "https://docs.google.com/document/d/doc123"})
    
    # 結果を取得
    result1 = context.get_result("task1")
    result2 = context.get_result("task2")
    full_context = context.get_context()
    
    print(f"✅ SharedContext動作確認")
    print(f"   task1結果: {result1}")
    print(f"   task2結果: {result2}")
    print(f"   ドキュメントURL: {full_context.get('document_url', 'N/A')}")
    print(f"   コンテキストキー数: {len(full_context)}")
    
    return True

async def main():
    """メイン実行関数"""
    print("\n" + "=" * 60)
    print("  ADKエージェント動作確認スクリプト")
    print("=" * 60)
    print("\nこのスクリプトは、実際のAPI統合（Vertex AI Search、Google Drive、")
    print("Google Chat/Gmail API）がなくても動作確認できます。\n")
    
    # ADKセットアップ確認
    adk_available = check_adk_setup()
    
    # 各エージェントのテスト
    results = []
    
    results.append(("SharedContext", await test_shared_context()))
    results.append(("ResearchAgent", await test_research_agent()))
    results.append(("AnalysisAgent", await test_analysis_agent()))
    results.append(("NotificationAgent", await test_notification_agent()))
    
    # 結果サマリー
    print_section("テスト結果サマリー")
    
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  {name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✅ すべてのテストが成功しました！")
        if adk_available:
            print("✅ ADKエージェントが正常に動作しています")
        else:
            print("⚠️  モックモードで動作しています（ADK未インストールまたはAPIキー未設定）")
    else:
        print("\n❌ 一部のテストが失敗しました。エラーログを確認してください。")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
