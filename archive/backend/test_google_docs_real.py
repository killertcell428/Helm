"""
Google Docs API実装の動作確認スクリプト

使用方法:
    # 環境変数が設定されていることを確認
    # .envファイルまたは環境変数に以下が設定されている必要があります:
    # GOOGLE_OAUTH_CREDENTIALS_FILE=path/to/oauth_credentials.json
    # GOOGLE_DRIVE_FOLDER_ID=your-folder-id
    # GOOGLE_CLOUD_PROJECT_ID=your-project-id
    
    python test_google_docs_real.py
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

from services.google_workspace import GoogleWorkspaceService
from utils.logger import logger


def test_google_docs_api():
    """Google Docs APIの動作確認"""
    print("=" * 60)
    print("Google Docs API 動作確認")
    print("=" * 60)
    
    # 環境変数の確認
    oauth_credentials_file = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE")
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    
    print(f"\n環境変数確認:")
    print(f"  GOOGLE_OAUTH_CREDENTIALS_FILE: {oauth_credentials_file}")
    print(f"  GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}")
    print(f"  GOOGLE_DRIVE_FOLDER_ID: {folder_id}")
    print(f"  GOOGLE_CLOUD_PROJECT_ID: {project_id}")
    
    if oauth_credentials_file and os.path.exists(oauth_credentials_file):
        print(f"\n✅ OAuth認証情報ファイルが見つかりました: {oauth_credentials_file}")
        if folder_id:
            print(f"✅ フォルダIDが設定されています: {folder_id}")
        else:
            print(f"\n⚠️  警告: GOOGLE_DRIVE_FOLDER_IDが設定されていません")
    elif credentials_path and os.path.exists(credentials_path):
        print(f"\n✅ サービスアカウント認証情報ファイルが見つかりました: {credentials_path}")
    else:
        print("\n⚠️  警告: 認証情報が設定されていません")
        print("   モックモードで動作します")
    
    # サービス初期化
    print("\n" + "-" * 60)
    print("Google Workspace サービスを初期化中...")
    workspace_service = GoogleWorkspaceService(folder_id=folder_id)
    
    if workspace_service.use_mock:
        print("📝 モックモードで動作します")
    else:
        if workspace_service.use_oauth:
            print("🔌 実APIモードで動作します（OAuth認証）")
        else:
            print("🔌 実APIモードで動作します（サービスアカウント）")
    
    # テスト1: ドキュメント生成
    print("\n" + "-" * 60)
    print("テスト1: ドキュメント生成")
    try:
        content = {
            "title": "3案比較資料 - テスト",
            "content": """
# 3案比較分析

## 継続案
- 期待収益: 1000
- 期待コスト: 800
- 期待利益: 200
- リスクレベル: 中

## 縮小案
- 期待収益: 700
- 期待コスト: 500
- 期待利益: 200
- リスクレベル: 低

## 撤退案
- 期待収益: 0
- 期待コスト: 100
- 期待利益: -100
- リスクレベル: 低
"""
        }
        result = workspace_service.generate_document(
            content=content,
            document_type="document"
        )
        print(f"✅ 成功: ドキュメントが生成されました")
        print(f"   - ドキュメントID: {result.get('document_id')}")
        print(f"   - タイトル: {result.get('title')}")
        print(f"   - 編集URL: {result.get('edit_url')}")
        print(f"   - 閲覧URL: {result.get('view_url')}")
        
        document_id = result.get('document_id')
        
        # テスト2: ドキュメントの確認（Google Driveで確認可能）
        print("\n" + "-" * 60)
        print("テスト2: ドキュメント確認")
        print(f"✅ ドキュメントが作成されました")
        print(f"   以下のURLで確認できます:")
        print(f"   - 編集: {result.get('edit_url')}")
        print(f"   - 閲覧: {result.get('view_url')}")
        
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
        success = test_google_docs_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
