"""
承認フローエンジン
テンプレートに基づく多段階承認（ステージ遷移・全員承認判定）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from utils.logger import logger


class ApprovalFlowEngine:
    """承認フローのステージ遷移と全員承認判定を行う。"""

    def __init__(self, definition_loader: Any = None):
        if definition_loader is None:
            from services.definition_loader import DefinitionLoader
            definition_loader = DefinitionLoader()
        self.loader = definition_loader

    def get_template(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """flow_id に対応するテンプレートを取得する。"""
        flows = self.loader.get_approval_flows()
        if not flows:
            return None
        for t in (flows.get("templates") or []):
            if t.get("flow_id") == flow_id:
                return t
        return None

    def get_initial_stage_id(self, template: Dict[str, Any]) -> str:
        """最初の承認待ちステージを返す（draft の next）。"""
        stages = template.get("stages") or []
        for s in stages:
            if s.get("stage_id") == "draft":
                return s.get("next") or "approved"
        return stages[0].get("next", "approved") if stages else "approved"

    def record_approval(
        self,
        escalation: Dict[str, Any],
        approver_role_id: str,
        decision: str,
    ) -> Dict[str, Any]:
        """
        承認または却下を記録し、ステージ遷移を行う。

        Args:
            escalation: エスカレーション（approval_flow_id, current_stage_id, stage_approvals を含む）
            approver_role_id: 承認者のロール ID（X-User-Role または body から）
            decision: "approve" or "reject"

        Returns:
            更新後の escalation のコピー。status が "approved" or "rejected" になった場合、フロー完了。
        """
        import copy as copy_module
        out = copy_module.deepcopy(escalation)
        flow_id = escalation.get("approval_flow_id")
        if not flow_id:
            return out
        template = self.get_template(flow_id)
        if not template:
            return out
        stages = template.get("stages") or []
        stage_by_id = {s["stage_id"]: s for s in stages}
        current_stage_id = escalation.get("current_stage_id")
        if not current_stage_id:
            current_stage_id = self.get_initial_stage_id(template)
            out["current_stage_id"] = current_stage_id
        current_stage = stage_by_id.get(current_stage_id)
        if not current_stage:
            return out
        approver_role_ids = current_stage.get("approver_role_ids") or []
        if approver_role_id not in approver_role_ids:
            logger.warning(f"Approver {approver_role_id} not in {approver_role_ids} for stage {current_stage_id}")
            return out
        if decision == "reject":
            out["status"] = "rejected"
            return out
        # approve: 記録を追加
        stage_approvals = dict(out.get("stage_approvals") or {})
        if current_stage_id not in stage_approvals:
            stage_approvals[current_stage_id] = []
        stage_approvals[current_stage_id].append({
            "role_id": approver_role_id,
            "approved_at": datetime.now().isoformat(),
        })
        out["stage_approvals"] = stage_approvals
        # 全員承認済みか
        approved_ids = {a.get("role_id") for a in stage_approvals.get(current_stage_id, [])}
        if approved_ids >= set(approver_role_ids):
            next_id = current_stage.get("next")
            out["current_stage_id"] = next_id
            if next_id is None or next_id == "approved":
                out["status"] = "approved"
        return out
