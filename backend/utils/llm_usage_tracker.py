"""
LLM日次トークン使用量の追跡と上限チェック
コスト暴騰防止のため、日次トークン数が上限を超えたらLLM呼び出しをスキップ（モックフォールバック）
"""

from datetime import datetime, date
from typing import Optional
import threading
from utils.logger import logger


class LLMUsageTracker:
    """日次トークン使用量を記録し、上限を超えたかチェックする"""

    def __init__(self, daily_limit: int = 0):
        """
        Args:
            daily_limit: 1日あたりのトークン上限。0は無制限。
        """
        self.daily_limit = daily_limit
        self._date: Optional[date] = None
        self._input_tokens = 0
        self._output_tokens = 0
        self._lock = threading.Lock()

    def add(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """使用トークンを加算。日付が変わっていればリセットする。"""
        if self.daily_limit <= 0:
            return
        with self._lock:
            today = date.today()
            if self._date != today:
                self._date = today
                self._input_tokens = 0
                self._output_tokens = 0
            self._input_tokens += input_tokens
            self._output_tokens += output_tokens
            total = self._input_tokens + self._output_tokens
            logger.debug(f"LLM usage: daily total={total}, limit={self.daily_limit}")

    def is_over_limit(self) -> bool:
        """本日の累積が上限を超えている場合 True。上限0の場合は常に False。"""
        if self.daily_limit <= 0:
            return False
        with self._lock:
            today = date.today()
            if self._date != today:
                return False
            total = self._input_tokens + self._output_tokens
            return total >= self.daily_limit

    def get_daily_total(self) -> int:
        """本日の累積トークン数（input + output）。"""
        with self._lock:
            today = date.today()
            if self._date != today:
                return 0
            return self._input_tokens + self._output_tokens


# モジュール単一インスタンス（config から初期化）
_usage_tracker: Optional[LLMUsageTracker] = None


def get_usage_tracker(daily_limit: int = 0) -> LLMUsageTracker:
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = LLMUsageTracker(daily_limit=daily_limit)
    return _usage_tracker
