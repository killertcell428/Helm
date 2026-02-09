"""
Google Chat API実装の動作確認スクリプト

使用方法:
    # 環境変数が設定されていることを確認
    # .envファイルまたは環境変数に以下が設定されている必要があります:
    # GOOGLE_OAUTH_CREDENTIALS_FILE=path/to/oauth_credentials.json
    # GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json（サービスアカウント使用時）
    # GOOGLE_CLOUD_PROJECT_ID=your-project-id
    
    python test_google_chat_real.py
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

from services.google_chat import GoogleChatService
from utils.logger import logger


def test_google_chat_api():
    """Google Chat APIの動作確認"""
    print("=" * 60)
    print("Google Chat API 動作確認")
    print("=" * 60)
    
    # 環境変数の確認
    oauth_credentials_file = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    
    print(f"\n環境変数確認:")
    print(f"  GOOGLE_OAUTH_CREDENTIALS_FILE: {oauth_credentials_file}")
    print(f"  GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}")
    print(f"  GOOGLE_CLOUD_PROJECT_ID: {project_id}")
    
    if oauth_credentials_file and os.path.exists(oauth_credentials_file):
        print(f"\n✅ OAuth認証情報ファイルが見つかりました: {oauth_credentials_file}")
    elif credentials_path and os.path.exists(credentials_path):
        print(f"\n✅ サービスアカウント認証情報ファイルが見つかりました: {credentials_path}")
    else:
        print("\n⚠️  警告: 認証情報が設定されていません")
        print("   モックモードで動作します")
    
    # サービス初期化
    print("\n" + "-" * 60)
    print("Google Chat サービスを初期化中...")
    chat_service = GoogleChatService()
    
    if chat_service.use_mock:
        print("📝 モックモードで動作します")
    else:
        if chat_service.use_oauth:
            print("🔌 実APIモードで動作します（OAuth認証）")
        else:
            print("🔌 実APIモードで動作します（サービスアカウント）")
    
    # テスト1: チャットメッセージ取得
    print("\n" + "-" * 60)
    print("テスト1: チャットメッセージ取得")
    print("\n⚠️  注意: Google Chat APIはGoogle Workspaceアカウントが必要な場合があります")
    print("   個人アカウントの場合、モックモードにフォールバックする可能性があります")
    print("\n📝 スペースIDの形式:")
    print("   - 形式1: spaces/{space_id} (例: spaces/AAAAxxxxxxx)")
    print("   - 形式2: {space_id} (例: AAAAxxxxxxx)")
    print("   - 実際のスペースIDは、Google ChatのスペースURLから取得できます")
    
    try:
        # テスト用のスペース名（実際のスペース名に置き換えてください）
        test_chat_id = input("\nテストするスペースIDを入力してください（Enterでスキップ、モックデータでテスト）: ").strip()
        
        if not test_chat_id:
            print("\n⚠️  テストをスキップします（スペースIDが必要です）")
            print("   モックデータで動作確認を行います")
            result = chat_service.get_chat_messages("test_chat_id", "テストチャンネル")
        else:
            print(f"\n📡 スペース '{test_chat_id}' からメッセージを取得中...")
            result = chat_service.get_chat_messages(test_chat_id, "テストチャンネル")
        
        # モックモードかどうかを確認
        if chat_service.use_mock or result.get('chat_id') == 'test_chat_id':
            print(f"\n📝 モックモードで動作しています")
        else:
            print(f"\n✅ 成功: チャットメッセージが取得されました（実API）")
        
        print(f"   - チャットID: {result.get('chat_id')}")
        print(f"   - チャンネル名: {result.get('channel_name')}")
        print(f"   - メッセージ数: {len(result.get('messages', []))}")
        
        # メッセージの一部を表示
        messages = result.get('messages', [])
        if messages:
            print(f"\n   最初の3件のメッセージ:")
            for i, msg in enumerate(messages[:3], 1):
                text = msg.get('text', '')
                if len(text) > 50:
                    text = text[:50] + "..."
                print(f"   {i}. [{msg.get('user', 'Unknown')}]: {text}")
        else:
            print("\n   ⚠️  メッセージがありません")
        
        # テスト2: メッセージパース
        print("\n" + "-" * 60)
        print("テスト2: メッセージパース")
        parsed = chat_service.parse_messages(messages)
        print(f"✅ 成功: メッセージをパースしました")
        print(f"   - 総メッセージ数: {parsed.get('total_messages')}")
        print(f"   - リスクメッセージ: {len(parsed.get('risk_messages', []))}件")
        print(f"   - 反対意見: {len(parsed.get('opposition_messages', []))}件")
        print(f"   - 懸念あり: {parsed.get('has_concern')}")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        print("\n💡 ヒント:")
        print("   - スペースIDが正しい形式か確認してください")
        print("   - Google Workspaceアカウントが必要な場合があります")
        print("   - 権限が不足している可能性があります")
        print("\n   エラーが発生した場合でも、モックモードで動作するはずです")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✅ すべてのテストが完了しました")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_google_chat_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
