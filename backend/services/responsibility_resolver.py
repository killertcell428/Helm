"""
RACI と承認フロー定義に基づき、分析結果に対する target_roles と approval_flow_id を解決する
"""

from typing import Dict, Any, List, Optional
from services.definition_loader import DefinitionLoader


class ResponsibilityResolver:
    """pattern_id から R（責任者）と flow_id を解決する。"""

    def __init__(self, loader: Optional[DefinitionLoader] = None):
        self.loader = loader or DefinitionLoader()

    def resolve(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析結果から target_roles と approval_flow_id を返す。

        Returns:
            { "target_roles": ["role_exec"], "approval_flow_id": "single_approval" }
        """
        default_result = {"target_roles": ["Executive"], "approval_flow_id": None}
        findings = analysis_result.get("findings") or []
        pattern_id = "default"
        if findings and isinstance(findings[0], dict):
            pattern_id = findings[0].get("pattern_id") or "default"

        raci = self.loader.get_raci()
        if not raci:
            return default_result
        decision_types = raci.get("decision_types") or []
        decision = next((d for d in decision_types if d.get("decision_type_id") == pattern_id), None)
        if not decision:
            decision = next((d for d in decision_types if d.get("decision_type_id") == "default"), None)
        if not decision:
            return default_result
        target_roles: List[str] = list(decision.get("R") or [])
        if not target_roles:
            target_roles = ["Executive"]

        approval_flows = self.loader.get_approval_flows()
        flow_id = None
        if approval_flows:
            templates = approval_flows.get("templates") or []
            for t in templates:
                ids = t.get("decision_type_ids") or []
                if pattern_id in ids or "default" in ids:
                    flow_id = t.get("flow_id")
                    break
            if not flow_id and templates:
                flow_id = templates[0].get("flow_id")

        return {"target_roles": target_roles, "approval_flow_id": flow_id}
