"""
OAuth認証トークンの取得スクリプト

初回のみ実行して、Googleアカウントで認証を行い、トークンを取得します。

使用方法:
    python setup_oauth_token.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

load_dotenv()

from services.google_drive_oauth import get_oauth_credentials


def main():
    """OAuth認証トークンを取得"""
    print("=" * 60)
    print("Google Drive OAuth認証トークンの取得")
    print("=" * 60)
    
    # 環境変数の確認
    oauth_credentials_file = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE")
    
    if not oauth_credentials_file:
        print("\n❌ エラー: GOOGLE_OAUTH_CREDENTIALS_FILE が設定されていません")
        print("\n.env ファイルに以下を追加してください:")
        print("GOOGLE_OAUTH_CREDENTIALS_FILE=C:\\path\\to\\oauth_credentials.json")
        return False
    
    if not os.path.exists(oauth_credentials_file):
        print(f"\n❌ エラー: 認証情報ファイルが見つかりません: {oauth_credentials_file}")
        print("\nOAuth 2.0 クライアントIDのJSONファイルをダウンロードして、")
        print("環境変数 GOOGLE_OAUTH_CREDENTIALS_FILE に設定してください。")
        print("\n詳細は SETUP_PERSONAL_DRIVE.md を参照してください。")
        return False
    
    print(f"\n認証情報ファイル: {oauth_credentials_file}")
    print("\nブラウザが開きます。Googleアカウントでログインして認証を完了してください。")
    print("（初回のみ必要です）")
    
    try:
        credentials = get_oauth_credentials(oauth_credentials_file)
        
        if credentials:
            print("\n✅ OAuth認証が完了しました！")
            print("トークンが保存されました。次回からは自動的に使用されます。")
            return True
        else:
            print("\n❌ OAuth認証に失敗しました")
            return False
            
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  認証が中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
