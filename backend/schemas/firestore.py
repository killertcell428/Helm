"""
Firestore スキーマ定義
組織構造、アラート、介入案、実行状態の保存
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class AlertStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class OrganizationStructure:
    """組織構造"""
    org_id: str
    nodes: List[Dict[str, Any]]  # [{id, type, role, name}]
    edges: List[Dict[str, Any]]  # [{from, to, relation}]
    created_at: str
    updated_at: str


@dataclass
class MeetingLog:
    """会議ログ"""
    meeting_id: str
    org_id: str
    transcript: str
    parsed_data: Dict[str, Any]
    metadata: Dict[str, Any]
    ingested_at: str


@dataclass
class ChatLog:
    """チャットログ"""
    chat_id: str
    org_id: str
    messages: List[Dict[str, Any]]
    parsed_data: Dict[str, Any]
    metadata: Dict[str, Any]
    ingested_at: str


@dataclass
class AnalysisResult:
    """分析結果"""
    analysis_id: str
    org_id: str
    meeting_id: str
    chat_id: Optional[str]
    findings: List[Dict[str, Any]]
    scores: Dict[str, float]
    overall_score: float
    severity: str
    explanation: str
    created_at: str
    status: str


@dataclass
class Alert:
    """アラート"""
    alert_id: str
    org_id: str
    analysis_id: str
    pattern_id: str
    severity: str
    overall_score: float
    alert_reasoning: str
    evaluation_explanation: str
    created_at: str
    status: AlertStatus


@dataclass
class Escalation:
    """エスカレーション"""
    escalation_id: str
    org_id: str
    alert_id: str
    analysis_id: str
    target_role: str
    reason: str
    created_at: str
    status: AlertStatus


@dataclass
class Approval:
    """承認"""
    approval_id: str
    org_id: str
    escalation_id: str
    decision: str
    modifications: Optional[Dict[str, Any]]
    created_at: str
    status: str


@dataclass
class Execution:
    """実行状態"""
    execution_id: str
    org_id: str
    approval_id: str
    status: ExecutionStatus
    progress: float
    tasks: List[Dict[str, Any]]
    results: Optional[List[Dict[str, Any]]]
    created_at: str
    updated_at: str
    completed_at: Optional[str]


class FirestoreSchema:
    """Firestoreスキーマ管理"""
    
    @staticmethod
    def to_firestore_dict(obj: Any) -> Dict[str, Any]:
        """データクラスをFirestore用の辞書に変換"""
        data = asdict(obj)
        # Enumを文字列に変換
        for key, value in data.items():
            if isinstance(value, Enum):
                data[key] = value.value
        return data
    
    @staticmethod
    def get_collection_paths() -> Dict[str, str]:
        """コレクションパスの定義"""
        return {
            "organizations": "organizations",
            "meetings": "organizations/{org_id}/meetings",
            "chats": "organizations/{org_id}/chats",
            "analyses": "organizations/{org_id}/analyses",
            "alerts": "organizations/{org_id}/alerts",
            "escalations": "organizations/{org_id}/escalations",
            "approvals": "organizations/{org_id}/approvals",
            "executions": "organizations/{org_id}/executions",
            "structure": "organizations/{org_id}/structure"
        }

