"""
監査ログ機能
いつ誰が何を見たかを記録
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
from utils.logger import logger
from utils.exceptions import ServiceError


class AuditAction(str, Enum):
    """監査アクション"""
    VIEW_ANALYSIS = "view_analysis"  # 分析結果の閲覧
    VIEW_MEETING = "view_meeting"  # 会議データの閲覧
    VIEW_CHAT = "view_chat"  # チャットデータの閲覧
    ESCALATE = "escalate"  # エスカレーション
    APPROVE = "approve"  # 承認
    REJECT = "reject"  # 却下
    EXECUTE = "execute"  # 実行


class AuditLogService:
    """監査ログサービス"""
    
    def __init__(self, log_dir: str = "logs/audit"):
        """
        Args:
            log_dir: ログディレクトリ
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        # メモリ内のログ（最近のログ）
        self.recent_logs: List[Dict[str, Any]] = []
        self.max_memory_logs = 1000
    
    def log(
        self,
        user_id: str,
        role: str,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        監査ログを記録
        
        Args:
            user_id: ユーザーID
            role: ロール
            action: アクション
            resource_type: リソースタイプ（analysis, meeting, chat等）
            resource_id: リソースID
            ip_address: IPアドレス
            device_info: デバイス情報
            details: 詳細情報
            
        Returns:
            ログID
        """
        log_id = str(datetime.now().timestamp())
        log_entry = {
            "log_id": log_id,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "role": role,
            "action": action.value,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "ip_address": ip_address,
            "device_info": device_info,
            "details": details or {}
        }
        
        # メモリに保存
        self.recent_logs.append(log_entry)
        if len(self.recent_logs) > self.max_memory_logs:
            self.recent_logs.pop(0)
        
        # ファイルに保存（JSONL形式）
        try:
            # ディレクトリが存在することを確認
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + "\n")
        except PermissionError as e:
            logger.error(f"Permission denied when writing audit log: {e}", exc_info=True)
        except OSError as e:
            logger.error(f"OS error when writing audit log: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}", exc_info=True)
            # エラー時もメモリには保存されているので続行
        
        logger.info(f"Audit log recorded: {action.value} by {user_id} ({role}) on {resource_type}:{resource_id}")
        
        return log_id
    
    def get_logs(
        self,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        監査ログを取得
        
        Args:
            user_id: ユーザーID（フィルタ）
            role: ロール（フィルタ）
            action: アクション（フィルタ）
            resource_type: リソースタイプ（フィルタ）
            resource_id: リソースID（フィルタ）
            start_time: 開始時刻（フィルタ）
            end_time: 終了時刻（フィルタ）
            limit: 取得件数
            
        Returns:
            監査ログのリスト
        """
        logs = []
        
        # ファイルから読み込み（最近のログのみ）
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if line.strip():
                            try:
                                log_entry = json.loads(line)
                                if isinstance(log_entry, dict):
                                    logs.append(log_entry)
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse audit log line {line_num}: {e}")
                                continue
            except PermissionError as e:
                logger.warning(f"Permission denied when reading audit log: {e}")
            except OSError as e:
                logger.warning(f"OS error when reading audit log: {e}")
            except Exception as e:
                logger.warning(f"Failed to read audit log: {e}", exc_info=True)
        
        # メモリ内のログも追加
        logs.extend(self.recent_logs)
        
        # フィルタリング
        filtered_logs = []
        for log_entry in logs:
            # 重複を避ける（log_idで判定）
            if any(l.get("log_id") == log_entry.get("log_id") for l in filtered_logs):
                continue
            
            # フィルタ条件をチェック
            if user_id and log_entry.get("user_id") != user_id:
                continue
            if role and log_entry.get("role") != role:
                continue
            if action and log_entry.get("action") != action.value:
                continue
            if resource_type and log_entry.get("resource_type") != resource_type:
                continue
            if resource_id and log_entry.get("resource_id") != resource_id:
                continue
            
            # 時刻フィルタ
            if start_time or end_time:
                log_time = datetime.fromisoformat(log_entry.get("timestamp", ""))
                if start_time and log_time < start_time:
                    continue
                if end_time and log_time > end_time:
                    continue
            
            filtered_logs.append(log_entry)
        
        # 時刻でソート（新しい順）
        filtered_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return filtered_logs[:limit]
    
    def get_user_activity(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        ユーザーの活動履歴を取得
        
        Args:
            user_id: ユーザーID
            days: 取得期間（日数）
            
        Returns:
            活動履歴のサマリー
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        logs = self.get_logs(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        # アクションごとの集計
        action_counts = {}
        for log in logs:
            action = log.get("action", "")
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_actions": len(logs),
            "action_counts": action_counts,
            "recent_logs": logs[:10]  # 最近10件
        }
