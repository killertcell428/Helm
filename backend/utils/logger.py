"""
ログ設定モジュール
Python標準のloggingモジュールを使用
構造化ログとコンテキスト情報をサポート
"""

import logging
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
import contextvars

# コンテキスト変数（リクエストID、ユーザーIDなど）
request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('request_id', default=None)
user_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('user_id', default=None)
endpoint_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('endpoint', default=None)
method_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('method', default=None)


class StructuredFormatter(logging.Formatter):
    """構造化ログフォーマッター（JSON形式）"""
    
    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをJSON形式にフォーマット"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # コンテキスト情報の追加
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id
        
        endpoint = endpoint_var.get()
        if endpoint:
            log_data["endpoint"] = endpoint
        
        method = method_var.get()
        if method:
            log_data["method"] = method
        
        # extra情報の追加
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # 例外情報の追加
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class ContextFilter(logging.Filter):
    """コンテキスト情報をログレコードに追加するフィルター"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """コンテキスト情報を追加"""
        request_id = request_id_var.get()
        if request_id:
            record.request_id = request_id
        
        user_id = user_id_var.get()
        if user_id:
            record.user_id = user_id
        
        endpoint = endpoint_var.get()
        if endpoint:
            record.endpoint = endpoint
        
        method = method_var.get()
        if method:
            record.method = method
        
        return True


def setup_logger(name: str = "helm", log_level: str = None, use_json: bool = None) -> logging.Logger:
    """
    ロガーを設定
    
    Args:
        name: ロガー名
        log_level: ログレベル（環境変数LOG_LEVELから取得、デフォルト: INFO）
        use_json: JSON形式のログを使用するか（環境変数LOG_FORMATから取得、デフォルト: false）
        
    Returns:
        設定済みロガー
    """
    logger = logging.getLogger(name)
    
    # 既に設定済みの場合はそのまま返す
    if logger.handlers:
        return logger
    
    # ログレベルの設定
    level = log_level or os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # JSON形式のログを使用するか
    if use_json is None:
        use_json = os.getenv("LOG_FORMAT", "text").lower() == "json"
    
    # ログフォーマット
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # コンテキストフィルターの追加
    context_filter = ContextFilter()
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(context_filter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラー（ログディレクトリが存在する場合）
    log_dir = Path("logs")
    if log_dir.exists() or os.getenv("ENABLE_FILE_LOGGING", "false").lower() == "true":
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"helm_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        logger.addHandler(file_handler)
        
        # JSON形式のログファイル（オプション）
        if use_json:
            json_log_file = log_dir / f"helm_{datetime.now().strftime('%Y%m%d')}.json.log"
            json_file_handler = RotatingFileHandler(
                json_log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            json_file_handler.setLevel(logging.DEBUG)
            json_file_handler.setFormatter(StructuredFormatter())
            json_file_handler.addFilter(context_filter)
            logger.addHandler(json_file_handler)
    
    return logger


def set_log_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None
):
    """
    ログコンテキストを設定
    
    Args:
        request_id: リクエストID
        user_id: ユーザーID
        endpoint: エンドポイント
        method: HTTPメソッド
    """
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if endpoint:
        endpoint_var.set(endpoint)
    if method:
        method_var.set(method)


def clear_log_context():
    """ログコンテキストをクリア"""
    request_id_var.set(None)
    user_id_var.set(None)
    endpoint_var.set(None)
    method_var.set(None)


# デフォルトロガー
logger = setup_logger()

