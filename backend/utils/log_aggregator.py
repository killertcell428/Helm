"""
ログ集約システム
JSON形式のログファイル出力と統計情報の生成
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from utils.logger import logger


class LogAggregator:
    """ログ集約と統計情報の生成"""
    
    def __init__(self, log_dir: str = "logs", enabled: bool = None):
        """
        ログ集約システムの初期化
        
        Args:
            log_dir: ログディレクトリのパス
            enabled: 有効化フラグ（環境変数LOG_AGGREGATION_ENABLEDから取得）
        """
        self.log_dir = Path(log_dir)
        if enabled is None:
            enabled = os.getenv("LOG_AGGREGATION_ENABLED", "false").lower() == "true"
        self.enabled = enabled
        
        if self.enabled:
            self.log_dir.mkdir(exist_ok=True)
            self.stats_file = self.log_dir / "log_stats.json"
            self.error_summary_file = self.log_dir / "error_summary.json"
    
    def aggregate_log(self, log_entry: Dict[str, Any]) -> None:
        """
        ログエントリを集約
        
        Args:
            log_entry: ログエントリ（JSON形式の辞書）
        """
        if not self.enabled:
            return
        
        try:
            # エラーログの集約
            if log_entry.get("level") in ["ERROR", "CRITICAL"]:
                self._aggregate_error(log_entry)
            
            # 統計情報の更新
            self._update_stats(log_entry)
            
        except Exception as e:
            logger.warning(f"Failed to aggregate log: {e}")
    
    def _aggregate_error(self, log_entry: Dict[str, Any]) -> None:
        """エラーログの集約"""
        try:
            # エラーサマリーファイルの読み込み
            error_summary = self._load_error_summary()
            
            # エラーコードでグループ化
            error_code = log_entry.get("extra_data", {}).get("error_code", "UNKNOWN")
            endpoint = log_entry.get("endpoint", "unknown")
            method = log_entry.get("method", "unknown")
            
            key = f"{error_code}:{method}:{endpoint}"
            
            if key not in error_summary:
                error_summary[key] = {
                    "error_code": error_code,
                    "endpoint": endpoint,
                    "method": method,
                    "count": 0,
                    "first_occurrence": log_entry.get("timestamp"),
                    "last_occurrence": log_entry.get("timestamp"),
                    "sample_messages": []
                }
            
            error_summary[key]["count"] += 1
            error_summary[key]["last_occurrence"] = log_entry.get("timestamp")
            
            # サンプルメッセージの保存（最大10件）
            if len(error_summary[key]["sample_messages"]) < 10:
                error_summary[key]["sample_messages"].append({
                    "timestamp": log_entry.get("timestamp"),
                    "message": log_entry.get("message"),
                    "request_id": log_entry.get("extra_data", {}).get("request_id")
                })
            
            # エラーサマリーの保存
            self._save_error_summary(error_summary)
            
        except Exception as e:
            logger.warning(f"Failed to aggregate error log: {e}")
    
    def _update_stats(self, log_entry: Dict[str, Any]) -> None:
        """統計情報の更新"""
        try:
            # 統計情報の読み込み
            stats = self._load_stats()
            
            # 日付キー
            date_key = datetime.now().strftime("%Y-%m-%d")
            
            if date_key not in stats:
                stats[date_key] = {
                    "total_logs": 0,
                    "by_level": defaultdict(int),
                    "by_endpoint": defaultdict(int),
                    "error_count": 0,
                    "warning_count": 0,
                    "info_count": 0,
                    "debug_count": 0
                }
            
            # 統計情報の更新
            stats[date_key]["total_logs"] += 1
            
            level = log_entry.get("level", "INFO")
            stats[date_key]["by_level"][level] += 1
            stats[date_key][f"{level.lower()}_count"] += 1
            
            endpoint = log_entry.get("endpoint", "unknown")
            stats[date_key]["by_endpoint"][endpoint] += 1
            
            # 統計情報の保存
            self._save_stats(stats)
            
        except Exception as e:
            logger.warning(f"Failed to update stats: {e}")
    
    def _load_stats(self) -> Dict[str, Any]:
        """統計情報の読み込み"""
        if not self.stats_file.exists():
            return {}
        
        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load stats: {e}")
            return {}
    
    def _save_stats(self, stats: Dict[str, Any]) -> None:
        """統計情報の保存"""
        try:
            # 古い統計情報の削除（30日以上前）
            cutoff_date = datetime.now() - timedelta(days=30)
            stats = {
                k: v for k, v in stats.items()
                if datetime.strptime(k, "%Y-%m-%d") >= cutoff_date
            }
            
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(stats, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save stats: {e}")
    
    def _load_error_summary(self) -> Dict[str, Any]:
        """エラーサマリーの読み込み"""
        if not self.error_summary_file.exists():
            return {}
        
        try:
            with open(self.error_summary_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load error summary: {e}")
            return {}
    
    def _save_error_summary(self, error_summary: Dict[str, Any]) -> None:
        """エラーサマリーの保存"""
        try:
            # エラー数が多い順にソート（最大100件）
            sorted_errors = sorted(
                error_summary.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:100]
            
            error_summary = dict(sorted_errors)
            
            with open(self.error_summary_file, "w", encoding="utf-8") as f:
                json.dump(error_summary, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save error summary: {e}")
    
    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        統計情報の取得
        
        Args:
            days: 取得する日数
        
        Returns:
            統計情報の辞書
        """
        stats = self._load_stats()
        
        # 指定日数分の統計情報を取得
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_stats = {
            k: v for k, v in stats.items()
            if datetime.strptime(k, "%Y-%m-%d") >= cutoff_date
        }
        
        return filtered_stats
    
    def get_error_summary(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        エラーサマリーの取得
        
        Args:
            limit: 取得するエラー数
        
        Returns:
            エラーサマリーのリスト
        """
        error_summary = self._load_error_summary()
        
        # エラー数が多い順にソート
        sorted_errors = sorted(
            error_summary.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:limit]
        
        return [{"key": k, **v} for k, v in sorted_errors]


# グローバルインスタンス
log_aggregator = LogAggregator()
