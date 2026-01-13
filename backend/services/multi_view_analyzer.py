"""
マルチ視点LLM分析サービス
複数ロール（executive / staff / corp_planning / governance など）で同一データを評価
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from utils.logger import logger
from services.llm_service import LLMService


@dataclass
class RoleConfig:
    """LLM評価ロール設定"""
    role_id: str
    weight: float


class MultiRoleLLMAnalyzer:
    """
    複数ロールをまとめてLLM評価するアナライザー
    
    - 同じ meeting_data / chat_data / materials_data を各ロール視点で評価
    - 各ロールは AnalysisResult スキーマに準拠したJSONを返す想定
    """

    def __init__(self, llm_service: LLMService, roles: Optional[List[RoleConfig]] = None) -> None:
        self.llm_service = llm_service
        # デフォルトのロール構成（重みはアンサンブル時に利用）
        self.roles: List[RoleConfig] = roles or [
            RoleConfig(role_id="executive", weight=0.4),
            RoleConfig(role_id="corp_planning", weight=0.3),
            RoleConfig(role_id="staff", weight=0.2),
            RoleConfig(role_id="governance", weight=0.1),
        ]

    def analyze_with_roles(
        self,
        meeting_data: Dict[str, Any],
        chat_data: Optional[Dict[str, Any]] = None,
        materials_data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        各ロール視点でLLM分析を実行
        
        Returns:
            [
              {
                "role_id": str,
                "weight": float,
                "analysis": { ... AnalysisResult dict ... }
              },
              ...
            ]
        """
        results: List[Dict[str, Any]] = []

        # LLMが無効な場合は空リストを返して、呼び出し元でルールベースのみで処理させる
        if not getattr(self.llm_service, "_vertex_ai_available", False):
            logger.info("LLM is not available; skipping multi-role analysis")
            return results

        for role in self.roles:
            try:
                logger.info(f"Running multi-view LLM analysis for role={role.role_id}")
                analysis = self.llm_service.analyze_structure(
                    meeting_data=meeting_data,
                    chat_data=chat_data,
                    materials_data=materials_data,
                    role_id=role.role_id,
                )

                # 期待スキーマを満たさないケースでも、最低限のガードだけして格納
                overall_score = analysis.get("overall_score", 0)
                severity = analysis.get("severity", "MEDIUM")
                urgency = analysis.get("urgency", "MEDIUM")

                results.append(
                    {
                        "role_id": role.role_id,
                        "weight": role.weight,
                        "overall_score": overall_score,
                        "severity": severity,
                        "urgency": urgency,
                        "explanation": analysis.get("explanation", ""),
                        "analysis": analysis,
                    }
                )
            except Exception as e:
                logger.error(
                    f"Multi-role analysis failed for role={role.role_id}: {e}",
                    exc_info=True,
                )
                # 1ロール失敗しても他ロールは継続
                continue

        return results

