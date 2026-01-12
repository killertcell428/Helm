"""
ログ設定モジュール
Python標準のloggingモジュールを使用
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = "helm", log_level: str = None) -> logging.Logger:
    """
    ロガーを設定
    
    Args:
        name: ロガー名
        log_level: ログレベル（環境変数LOG_LEVELから取得、デフォルト: INFO）
        
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
    
    # ログフォーマット
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
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
        logger.addHandler(file_handler)
    
    return logger

# デフォルトロガー
logger = setup_logger()

