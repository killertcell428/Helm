"""
エラー通知機能
将来的な拡張用のプラグイン構造（メール、Slack、Webhookなど）
現在はログファイルへの記録のみ実装
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from utils.logger import logger


class ErrorNotifier(ABC):
    """エラー通知の基底クラス"""
    
    @abstractmethod
    def notify(self, error_data: Dict[str, Any]) -> bool:
        """
        エラー通知を送信
        
        Args:
            error_data: エラーデータ
        
        Returns:
            通知が成功したかどうか
        """
        pass


class LogFileNotifier(ErrorNotifier):
    """ログファイルへのエラー通知"""
    
    def __init__(self, log_dir: str = "logs", enabled: bool = None):
        """
        ログファイル通知の初期化
        
        Args:
            log_dir: ログディレクトリのパス
            enabled: 有効化フラグ（環境変数ERROR_NOTIFICATION_ENABLEDから取得）
        """
        self.log_dir = Path(log_dir)
        if enabled is None:
            enabled = os.getenv("ERROR_NOTIFICATION_ENABLED", "true").lower() == "true"
        self.enabled = enabled
        self.error_log_file = self.log_dir / "error_notifications.json"

        # Cloud Run など書き込み不可環境ではファイル通知を無効化
        if self.enabled:
            try:
                self.log_dir.mkdir(exist_ok=True)
                # 実際に書けるかテスト（Cloud Run の / は読み取り専用）
                test_file = self.log_dir / ".write_test"
                test_file.write_text("")
                test_file.unlink()
            except (PermissionError, OSError) as e:
                logger.info(
                    f"Error notification file logging disabled (read-only env): {e}. "
                    "Errors will still be logged to stdout."
                )
                self.enabled = False
    
    def notify(self, error_data: Dict[str, Any]) -> bool:
        """ログファイルにエラー通知を記録"""
        if not self.enabled:
            return False
        
        try:
            # エラーログの読み込み
            error_logs = self._load_error_logs()
            
            # エラーログの追加
            error_log = {
                "timestamp": datetime.now().isoformat(),
                "error_data": error_data
            }
            error_logs.append(error_log)
            
            # 古いログの削除（1000件を超える場合）
            if len(error_logs) > 1000:
                error_logs = error_logs[-1000:]
            
            # エラーログの保存
            self._save_error_logs(error_logs)
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to log error notification: {e}")
            return False
    
    def _load_error_logs(self) -> List[Dict[str, Any]]:
        """エラーログの読み込み"""
        if not self.error_log_file.exists():
            return []
        
        try:
            with open(self.error_log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load error logs: {e}")
            return []
    
    def _save_error_logs(self, error_logs: List[Dict[str, Any]]) -> None:
        """エラーログの保存"""
        try:
            with open(self.error_log_file, "w", encoding="utf-8") as f:
                json.dump(error_logs, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save error logs: {e}")


class EmailNotifier(ErrorNotifier):
    """メール通知（将来の実装用）"""
    
    def notify(self, error_data: Dict[str, Any]) -> bool:
        """メール通知を送信（未実装）"""
        # 将来の実装用
        logger.info("Email notification not implemented yet")
        return False


class SlackNotifier(ErrorNotifier):
    """Slack通知（将来の実装用）"""
    
    def notify(self, error_data: Dict[str, Any]) -> bool:
        """Slack通知を送信（未実装）"""
        # 将来の実装用
        logger.info("Slack notification not implemented yet")
        return False


class WebhookNotifier(ErrorNotifier):
    """Webhook通知（将来の実装用）"""
    
    def notify(self, error_data: Dict[str, Any]) -> bool:
        """Webhook通知を送信（未実装）"""
        # 将来の実装用
        logger.info("Webhook notification not implemented yet")
        return False


class ErrorNotificationManager:
    """エラー通知マネージャー"""
    
    def __init__(self):
        """エラー通知マネージャーの初期化"""
        self.notifiers: List[ErrorNotifier] = []
        
        # ログファイル通知（デフォルトで有効）
        log_notifier = LogFileNotifier()
        if log_notifier.enabled:
            self.notifiers.append(log_notifier)
        
        # メール通知（環境変数で有効化可能）
        if os.getenv("ERROR_NOTIFICATION_EMAIL_ENABLED", "false").lower() == "true":
            email_notifier = EmailNotifier()
            self.notifiers.append(email_notifier)
        
        # Slack通知（環境変数で有効化可能）
        if os.getenv("ERROR_NOTIFICATION_SLACK_ENABLED", "false").lower() == "true":
            slack_notifier = SlackNotifier()
            self.notifiers.append(slack_notifier)
        
        # Webhook通知（環境変数で有効化可能）
        if os.getenv("ERROR_NOTIFICATION_WEBHOOK_ENABLED", "false").lower() == "true":
            webhook_notifier = WebhookNotifier()
            self.notifiers.append(webhook_notifier)
    
    def notify_error(self, error_data: Dict[str, Any]) -> bool:
        """
        エラー通知を送信
        
        Args:
            error_data: エラーデータ
        
        Returns:
            少なくとも1つの通知が成功したかどうか
        """
        success_count = 0
        
        for notifier in self.notifiers:
            try:
                if notifier.notify(error_data):
                    success_count += 1
            except Exception as e:
                logger.warning(f"Failed to send error notification via {type(notifier).__name__}: {e}")
        
        return success_count > 0
    
    def add_notifier(self, notifier: ErrorNotifier) -> None:
        """
        通知を追加
        
        Args:
            notifier: エラー通知インスタンス
        """
        self.notifiers.append(notifier)


# グローバルインスタンス
error_notification_manager = ErrorNotificationManager()
