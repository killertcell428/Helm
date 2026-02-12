"""
データ保存期間に基づく自動削除
設計: docs/data-retention.md
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from utils.logger import logger


def _parse_date(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        s = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def run_retention_cleanup(
    meetings_db: Dict[str, Dict],
    chats_db: Dict[str, Dict],
    materials_db: Dict[str, Dict],
    analyses_db: Dict[str, Dict],
    escalations_db: Dict[str, Dict],
    approvals_db: Dict[str, Dict],
    executions_db: Dict[str, Dict],
    retention_days: Dict[str, int],
) -> Dict[str, int]:
    """
    各ストアから保持日数を超えたレコードを削除する。
    参照整合性のため、executions → approvals → escalations → analyses → meetings/chats/materials の順で削除。

    Args:
        *_db: 各ストア（in-place で削除する）
        retention_days: ストア名 → 保持日数のマップ

    Returns:
        ストア名 → 削除件数
    """
    now = datetime.now()
    deleted: Dict[str, int] = {}

    def cutoff_days(days: int) -> datetime:
        return now - timedelta(days=days)

    def remove_expired(
        db: Dict[str, Dict],
        key_date_field: str,
        days: int,
        store_name: str,
    ) -> int:
        if days <= 0:
            return 0
        cutoff = cutoff_days(days)
        to_remove = []
        for k, v in db.items():
            if not isinstance(v, dict):
                continue
            dt = _parse_date(v.get(key_date_field) or v.get("created_at") or v.get("updated_at"))
            if dt and dt < cutoff:
                to_remove.append(k)
        for k in to_remove:
            del db[k]
        deleted[store_name] = len(to_remove)
        if to_remove:
            logger.info(f"Retention cleanup: {store_name} removed {len(to_remove)} keys")
        return len(to_remove)

    # 順序: 子から親
    remove_expired(
        executions_db,
        "created_at",
        retention_days.get("executions", 365),
        "executions_db",
    )
    remove_expired(
        approvals_db,
        "created_at",
        retention_days.get("approvals", 365),
        "approvals_db",
    )
    remove_expired(
        escalations_db,
        "created_at",
        retention_days.get("escalations", 365),
        "escalations_db",
    )
    remove_expired(
        analyses_db,
        "created_at",
        retention_days.get("analyses", 180),
        "analyses_db",
    )
    remove_expired(
        meetings_db,
        "ingested_at",
        retention_days.get("meetings", 90),
        "meetings_db",
    )
    remove_expired(
        chats_db,
        "ingested_at",
        retention_days.get("chats", 90),
        "chats_db",
    )
    remove_expired(
        materials_db,
        "ingested_at",
        retention_days.get("materials", 90),
        "materials_db",
    )

    return deleted
