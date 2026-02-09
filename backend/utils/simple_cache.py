"""
シンプルなインメモリ TTL キャッシュ。
API レスポンスのキャッシュ用（開発・テストおよび単一プロセス運用を想定）。
"""

import os
import time
import threading
from typing import Any, Optional

# デフォルト TTL（秒）。環境変数 CACHE_TTL_SECONDS で上書き可能
DEFAULT_ANALYSIS_CACHE_TTL = int(os.getenv("CACHE_ANALYSIS_TTL_SECONDS", "300"))  # 5分
DEFAULT_RESULTS_CACHE_TTL = int(os.getenv("CACHE_RESULTS_TTL_SECONDS", "300"))    # 5分


class TTLCache:
    """スレッドセーフな TTL 付きキーバリューキャッシュ。"""

    def __init__(self, ttl_seconds: int, max_size: int = 1000):
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._data: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._data:
                return None
            value, expires_at = self._data[key]
            if time.monotonic() > expires_at:
                del self._data[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            # サイズ制限: 古いエントリを削除（簡易的には先頭から）
            while len(self._data) >= self._max_size and self._data:
                oldest = next(iter(self._data))
                del self._data[oldest]
            self._data[key] = (value, time.monotonic() + self._ttl)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)


# 分析結果キャッシュ（GET /api/analysis/{id}）
analysis_cache: TTLCache = TTLCache(ttl_seconds=DEFAULT_ANALYSIS_CACHE_TTL)

# 実行結果キャッシュ（GET /api/execution/{id}/results、完了時のみ）
execution_results_cache: TTLCache = TTLCache(ttl_seconds=DEFAULT_RESULTS_CACHE_TTL)
