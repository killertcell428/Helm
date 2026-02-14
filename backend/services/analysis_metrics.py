"""
分析メトリクスの記録と取得
会議1件あたりのレイテンシ・LLM呼び出し回数・トークン数
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque
from utils.logger import logger

# 直近 N 件の分析メトリクスを保持（メモリ bounded）
MAX_RECORDS = 500


class AnalysisMetrics:
    """分析ごとのレイテンシ・トークン数を記録し、集計を返す"""

    def __init__(self, max_records: int = MAX_RECORDS):
        self.max_records = max_records
        self._records: deque = deque(maxlen=max_records)

    def record(
        self,
        analysis_id: str,
        latency_ms: int,
        llm_calls: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """1件の分析結果を記録"""
        entry = {
            "analysis_id": analysis_id,
            "latency_ms": latency_ms,
            "llm_calls": llm_calls,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "recorded_at": datetime.now().isoformat(),
        }
        self._records.append(entry)

    def get_usage_stats(self, last_n: Optional[int] = None) -> Dict[str, Any]:
        """
        直近の分析メトリクスを集計して返す。
        last_n を指定した場合は直近 last_n 件で集計。未指定時は全件。
        """
        records = list(self._records)
        if last_n is not None and last_n > 0:
            records = records[-last_n:]

        if not records:
            return {
                "count": 0,
                "avg_latency_ms": 0,
                "total_llm_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
            }

        count = len(records)
        total_latency = sum(r["latency_ms"] for r in records)
        total_llm_calls = sum(r["llm_calls"] for r in records)
        total_input = sum(r["input_tokens"] for r in records)
        total_output = sum(r["output_tokens"] for r in records)

        return {
            "count": count,
            "avg_latency_ms": round(total_latency / count, 2),
            "total_llm_calls": total_llm_calls,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
        }
