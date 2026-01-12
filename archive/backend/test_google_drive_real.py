"""
Google Drive API実装の動作確認スクリプト

使用方法:
    # 環境変数が設定されていることを確認
    # .envファイルまたは環境変数に以下が設定されている必要があります:
    # GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
    # GOOGLE_CLOUD_PROJECT_ID=your-project-id
    
    python test_google_drive_real.py
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

from services.google_drive import GoogleDriveService
from utils.logger import logger


def test_google_drive_api():
    """Google Drive APIの動作確認"""
    print("=" * 60)
    print("Google Drive API 動作確認")
    print("=" * 60)
    
    # 環境変数の確認
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    oauth_credentials_file = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE")
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    shared_drive_id = os.getenv("GOOGLE_DRIVE_SHARED_DRIVE_ID")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    
    print(f"\n環境変数確認:")
    print(f"  GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}")
    print(f"  GOOGLE_OAUTH_CREDENTIALS_FILE: {oauth_credentials_file}")
    print(f"  GOOGLE_DRIVE_FOLDER_ID: {folder_id}")
    print(f"  GOOGLE_DRIVE_SHARED_DRIVE_ID: {shared_drive_id}")
    print(f"  GOOGLE_CLOUD_PROJECT_ID: {project_id}")
    
    if oauth_credentials_file and os.path.exists(oauth_credentials_file):
        print(f"\n✅ OAuth認証情報ファイルが見つかりました: {oauth_credentials_file}")
        if folder_id:
            print(f"✅ フォルダIDが設定されています: {folder_id}")
        else:
            print(f"\n⚠️  警告: GOOGLE_DRIVE_FOLDER_IDが設定されていません")
            print("   個人フォルダに保存する場合はフォルダIDが必要です")
    elif credentials_path and os.path.exists(credentials_path):
        print(f"\n✅ サービスアカウント認証情報ファイルが見つかりました: {credentials_path}")
        if shared_drive_id:
            print(f"✅ 共有ドライブIDが設定されています: {shared_drive_id}")
        else:
            print(f"\n⚠️  警告: GOOGLE_DRIVE_SHARED_DRIVE_IDが設定されていません")
            print("   サービスアカウント使用時は共有ドライブが必要です")
    else:
        print("\n⚠️  警告: 認証情報が設定されていません")
        print("   モックモードで動作します")
    
    # サービス初期化
    print("\n" + "-" * 60)
    print("Google Drive サービスを初期化中...")
    drive_service = GoogleDriveService()
    
    if drive_service.use_mock:
        print("📝 モックモードで動作します")
    else:
        print("🔌 実APIモードで動作します")
    
    # テスト1: ファイル保存（モックデータ）
    print("\n" + "-" * 60)
    print("テスト1: ファイル保存")
    try:
        test_content = b"This is a test file content for Google Drive API."
        result = drive_service.save_file(
            file_name="test_file.txt",
            content=test_content,
            mime_type="text/plain"
        )
        print(f"✅ 成功: ファイルが保存されました")
        print(f"   - ファイルID: {result.get('file_id')}")
        print(f"   - ファイル名: {result.get('file_name')}")
        print(f"   - ダウンロードURL: {result.get('download_url')}")
        
        file_id = result.get('file_id')
        
        # テスト2: ダウンロードURL取得
        print("\n" + "-" * 60)
        print("テスト2: ダウンロードURL取得")
        download_url = drive_service.get_file_download_url(file_id)
        print(f"✅ 成功: ダウンロードURLを取得しました")
        print(f"   - URL: {download_url}")
        
        # テスト3: ファイル共有（実APIモードの場合のみ）
        if not drive_service.use_mock:
            print("\n" + "-" * 60)
            print("テスト3: ファイル共有（スキップ - テスト用メールアドレスが必要）")
            print("   実際のメールアドレスでテストする場合は、以下をコメントアウトしてください")
            # share_result = drive_service.share_file(
            #     file_id=file_id,
            #     emails=["test@example.com"],
            #     role="reader"
            # )
            # print(f"✅ 成功: ファイルを共有しました")
            # print(f"   - 共有先: {share_result.get('shared_with')}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✅ すべてのテストが完了しました")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_google_drive_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
