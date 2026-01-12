"""
Google Drive API - OAuth認証ヘルパー
個人のGoogleアカウントでGoogle Driveを使用するためのOAuth認証処理
"""

import os
import json
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from utils.logger import logger

# OAuth 2.0 スコープ
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',  # Google Drive API
    'https://www.googleapis.com/auth/documents',   # Google Docs API
    'https://www.googleapis.com/auth/chat.messages.readonly',  # Google Chat API（読み取り専用）
    'https://www.googleapis.com/auth/meetings.space.readonly',  # Google Meet API（読み取り専用）
]


def get_oauth_credentials(
    credentials_file: str,
    token_file: Optional[str] = None
) -> Optional[Credentials]:
    """
    OAuth認証情報を取得
    
    Args:
        credentials_file: OAuth 2.0 クライアントIDのJSONファイルパス
        token_file: トークンファイルのパス（Noneの場合は自動生成）
        
    Returns:
        OAuth認証情報、またはNone（認証失敗時）
    """
    if token_file is None:
        # デフォルトのトークンファイルパス
        token_file = os.path.join(
            os.path.dirname(credentials_file),
            'token.json'
        )
    
    creds = None
    
    # 既存のトークンファイルがあるか確認
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            logger.info(f"OAuth認証: 既存のトークンファイルを読み込みました: {token_file}")
        except Exception as e:
            logger.warning(f"OAuth認証: トークンファイルの読み込みに失敗しました: {e}")
    
    # トークンが無効または存在しない場合、再認証
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # トークンをリフレッシュ
            try:
                creds.refresh(Request())
                logger.info("OAuth認証: トークンをリフレッシュしました")
            except Exception as e:
                logger.warning(f"OAuth認証: トークンのリフレッシュに失敗しました: {e}")
                creds = None
        
        if not creds:
            # 新しい認証フローを開始
            if not os.path.exists(credentials_file):
                logger.error(f"OAuth認証: 認証情報ファイルが見つかりません: {credentials_file}")
                return None
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, SCOPES
                )
                # ローカルサーバーで認証（ブラウザが自動的に開く）
                creds = flow.run_local_server(
                    port=0,
                    open_browser=True,
                    prompt='consent'
                )
                logger.info("OAuth認証: 新しい認証が完了しました")
            except Exception as e:
                logger.error(f"OAuth認証: 認証フローの実行に失敗しました: {e}")
                return None
        
        # トークンを保存
        try:
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
            logger.info(f"OAuth認証: トークンを保存しました: {token_file}")
        except Exception as e:
            logger.warning(f"OAuth認証: トークンの保存に失敗しました: {e}")
    
    return creds
