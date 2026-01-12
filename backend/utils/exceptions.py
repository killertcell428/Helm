"""
カスタム例外クラスの定義
"""

from typing import Optional, Dict, Any


class HelmException(Exception):
    """Helmアプリケーションの基底例外クラス"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            message: エラーメッセージ
            error_code: エラーコード
            details: 詳細情報
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(HelmException):
    """バリデーションエラー"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field, **(details or {})}
        )
        self.field = field


class ServiceError(HelmException):
    """サービス呼び出しエラー"""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="SERVICE_ERROR",
            details={"service_name": service_name, **(details or {})}
        )
        self.service_name = service_name


class TimeoutError(HelmException):
    """タイムアウトエラー"""
    
    def __init__(self, message: str, timeout_seconds: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            details={"timeout_seconds": timeout_seconds, **(details or {})}
        )
        self.timeout_seconds = timeout_seconds


class NotFoundError(HelmException):
    """リソースが見つからないエラー"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class RetryableError(HelmException):
    """リトライ可能なエラー"""
    
    def __init__(
        self,
        message: str,
        max_retries: int = 3,
        retry_after: int = 1,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="RETRYABLE_ERROR",
            details={"max_retries": max_retries, "retry_after": retry_after, **(details or {})}
        )
        self.max_retries = max_retries
        self.retry_after = retry_after

