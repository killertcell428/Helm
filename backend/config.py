"""
設定ファイル
環境変数からの設定読み込みとデフォルト値の設定
"""

import os
import json
from typing import Optional, List, Dict, Any


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
    # 環境変数から取得、デフォルトはlocalhostとVercelのURL
    _cors_origins_str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,https://v0-helm-pdca-demo.vercel.app"
    )
    CORS_ORIGINS: list = [origin.strip() for origin in _cors_origins_str.split(",") if origin.strip()]
    
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

    # 取得範囲ホワイトリスト（空の場合は全件許可。カンマ区切りで meeting_id または chat_id を指定）
    INGEST_MEETING_IDS_WHITELIST: list = [
        x.strip() for x in os.getenv("INGEST_MEETING_IDS_WHITELIST", "").split(",") if x.strip()
    ]
    INGEST_CHAT_IDS_WHITELIST: list = [
        x.strip() for x in os.getenv("INGEST_CHAT_IDS_WHITELIST", "").split(",") if x.strip()
    ]

    # サプレッション: 検知を抑制する条件。JSON配列で [{"pattern_id":"X","meeting_id":"m1"}, ...]。resource 指定が無い場合はその pattern を全件抑制
    _suppression_json = os.getenv("SUPPRESSION_RULES", "[]")
    SUPPRESSION_RULES: List[Dict[str, Any]] = []
    try:
        if _suppression_json.strip():
            SUPPRESSION_RULES = json.loads(_suppression_json)
            if not isinstance(SUPPRESSION_RULES, list):
                SUPPRESSION_RULES = []
    except json.JSONDecodeError:
        SUPPRESSION_RULES = []

    # API Key 認証（JSON配列: [{"key":"xxx","role":"operator"}, ...]。空なら認証無効）
    _api_keys_json = os.getenv("API_KEYS", "[]")
    API_KEYS: List[Dict[str, str]] = []
    try:
        if _api_keys_json.strip():
            API_KEYS = json.loads(_api_keys_json)
            if not isinstance(API_KEYS, list):
                API_KEYS = []
    except json.JSONDecodeError:
        API_KEYS = []

    # データ保存期間（日数）。未設定時はデフォルト値
    RETENTION_DAYS_MEETINGS: int = int(os.getenv("RETENTION_DAYS_MEETINGS", "90"))
    RETENTION_DAYS_CHATS: int = int(os.getenv("RETENTION_DAYS_CHATS", "90"))
    RETENTION_DAYS_MATERIALS: int = int(os.getenv("RETENTION_DAYS_MATERIALS", "90"))
    RETENTION_DAYS_ANALYSES: int = int(os.getenv("RETENTION_DAYS_ANALYSES", "180"))
    RETENTION_DAYS_ESCALATIONS: int = int(os.getenv("RETENTION_DAYS_ESCALATIONS", "365"))
    RETENTION_DAYS_APPROVALS: int = int(os.getenv("RETENTION_DAYS_APPROVALS", "365"))
    RETENTION_DAYS_EXECUTIONS: int = int(os.getenv("RETENTION_DAYS_EXECUTIONS", "365"))
    
    # LLM統合設定
    USE_LLM: bool = os.getenv("USE_LLM", "false").lower() == "true"  # LLM統合を有効化
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-3-flash-preview")  # 使用するモデル（Gemini 3 Flash - 最新の推論モデル、Gen AI SDKではmodels/プレフィックス不要）
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "3"))  # 最大リトライ回数
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "60"))  # タイムアウト時間（秒）
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))  # 温度パラメータ
    LLM_TOP_P: float = float(os.getenv("LLM_TOP_P", "0.95"))  # Top-pサンプリング
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "outputs")  # 出力ファイルの保存ディレクトリ
    
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

