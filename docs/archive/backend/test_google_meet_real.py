"""
Google Meet API実装の動作確認スクリプト

使用方法:
    # 環境変数が設定されていることを確認
    # .envファイルまたは環境変数に以下が設定されている必要があります:
    # GOOGLE_OAUTH_CREDENTIALS_FILE=path/to/oauth_credentials.json
    # GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json（サービスアカウント使用時）
    # GOOGLE_CLOUD_PROJECT_ID=your-project-id
    
    python test_google_meet_real.py
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

from services.google_meet import GoogleMeetService
from utils.logger import logger


def test_google_meet_api():
    """Google Meet APIの動作確認"""
    print("=" * 60)
    print("Google Meet API 動作確認")
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
    print("Google Meet サービスを初期化中...")
    meet_service = GoogleMeetService()
    
    if meet_service.use_mock:
        print("📝 モックモードで動作します")
    else:
        if meet_service.use_oauth:
            print("🔌 実APIモードで動作します（OAuth認証）")
        else:
            print("🔌 実APIモードで動作します（サービスアカウント）")
    
    # テスト1: 議事録取得
    print("\n" + "-" * 60)
    print("テスト1: 議事録取得")
    print("\n⚠️  注意: Google Meet APIはGoogle Workspaceアカウントが必要な場合があります")
    print("   個人アカウントの場合、モックモードにフォールバックする可能性があります")
    print("\n📝 会議IDの形式:")
    print("   - 会議コード: 例) abc-defg-hij")
    print("   - 会議名: 例) 四半期経営会議")
    print("   - 実際の会議IDは、Google Meetの会議URLから取得できます")
    
    try:
        # テスト用の会議ID（実際の会議IDに置き換えてください）
        test_meeting_id = input("\nテストする会議IDを入力してください（Enterでスキップ、モックデータでテスト）: ").strip()
        
        if not test_meeting_id:
            print("\n⚠️  テストをスキップします（会議IDが必要です）")
            print("   モックデータで動作確認を行います")
            result = meet_service.get_transcript("test_meeting_id")
        else:
            print(f"\n📡 会議 '{test_meeting_id}' から議事録を取得中...")
            result = meet_service.get_transcript(test_meeting_id)
        
        # モックモードかどうかを確認
        if meet_service.use_mock or result.get('meeting_id') == 'test_meeting_id':
            print(f"\n📝 モックモードで動作しています")
        else:
            print(f"\n✅ 成功: 議事録が取得されました（実API）")
        
        print(f"   - 会議ID: {result.get('meeting_id')}")
        print(f"   - 会議名: {result.get('metadata', {}).get('meeting_name', 'N/A')}")
        print(f"   - 日付: {result.get('metadata', {}).get('date', 'N/A')}")
        print(f"   - 参加者数: {len(result.get('metadata', {}).get('participants', []))}")
        
        # 議事録の一部を表示
        transcript = result.get('transcript', '')
        if transcript:
            lines = transcript.strip().split('\n')[:5]  # 最初の5行
            print(f"\n   議事録の一部（最初の5行）:")
            for i, line in enumerate(lines, 1):
                if line.strip():
                    print(f"   {i}. {line.strip()[:60]}...")
        else:
            print("\n   ⚠️  議事録がありません")
        
        # テスト2: 議事録パース
        print("\n" + "-" * 60)
        print("テスト2: 議事録パース")
        parsed = meet_service.parse_transcript(transcript)
        print(f"✅ 成功: 議事録をパースしました")
        print(f"   - 総発言数: {parsed.get('total_statements')}")
        print(f"   - KPI言及: {len(parsed.get('kpi_mentions', []))}件")
        print(f"   - 撤退議論: {parsed.get('exit_discussed')}")
        
        if parsed.get('kpi_mentions'):
            print(f"\n   KPI言及の例:")
            for i, mention in enumerate(parsed.get('kpi_mentions', [])[:3], 1):
                print(f"   {i}. [{mention.get('speaker')}]: {mention.get('keyword')}")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        print("\n💡 ヒント:")
        print("   - 会議IDが正しい形式か確認してください")
        print("   - Google Workspaceアカウントが必要な場合があります")
        print("   - 権限が不足している可能性があります")
        print("   - 会議が終了している必要があります")
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
        success = test_google_meet_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
