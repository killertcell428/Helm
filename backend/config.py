"""
設定ファイル
環境変数からの設定読み込みとデフォルト値の設定
"""

import os
from typing import Optional


class Config:
    """アプリケーション設定"""
    
    # API設定
    API_TITLE: str = os.getenv("API_TITLE", "Helm API")
    API_VERSION: str = os.getenv("API_VERSION", "0.1.0")
    
    # ログ設定
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_FILE_LOGGING: bool = os.getenv("ENABLE_FILE_LOGGING", "false").lower() == "true"
    
    # タイムアウト設定（秒）
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "60"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "300"))  # LLM処理のタイムアウト（5分）
    EXECUTION_TIMEOUT: int = int(os.getenv("EXECUTION_TIMEOUT", "600"))  # 実行処理のタイムアウト（10分）
    
    # リトライ設定
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_BASE: float = float(os.getenv("RETRY_BACKOFF_BASE", "2.0"))
    RETRY_INITIAL_DELAY: float = float(os.getenv("RETRY_INITIAL_DELAY", "1.0"))
    
    # CORS設定
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,https://*.vercel.app"
    ).split(",")
    
    # Google Cloud設定
    GOOGLE_CLOUD_PROJECT_ID: Optional[str] = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    GOOGLE_DRIVE_SHARED_DRIVE_ID: Optional[str] = os.getenv("GOOGLE_DRIVE_SHARED_DRIVE_ID")  # 共有ドライブID（サービスアカウント使用時は必須）
    
    # OAuth認証設定（個人のGoogleアカウント使用時）
    GOOGLE_OAUTH_CREDENTIALS_FILE: Optional[str] = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE")  # OAuth 2.0 クライアントIDのJSONファイル
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = os.getenv("GOOGLE_DRIVE_FOLDER_ID")  # 個人フォルダID（OAuth認証使用時）
    
    # エスカレーション設定
    ESCALATION_THRESHOLD: int = int(os.getenv("ESCALATION_THRESHOLD", "70"))  # エスカレーション閾値
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"  # デモモード: findingsがあれば常にエスカレーション
    
    @classmethod
    def get_timeout(cls, timeout_type: str = "default") -> int:
        """
        タイムアウト値を取得
        
        Args:
            timeout_type: タイムアウトタイプ（default, llm, execution）
            
        Returns:
            タイムアウト値（秒）
        """
        timeout_map = {
            "default": cls.DEFAULT_TIMEOUT,
            "llm": cls.LLM_TIMEOUT,
            "execution": cls.EXECUTION_TIMEOUT
        }
        return timeout_map.get(timeout_type, cls.DEFAULT_TIMEOUT)


# グローバル設定インスタンス
config = Config()

