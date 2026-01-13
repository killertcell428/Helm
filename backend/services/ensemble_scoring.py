"""
アンサンブルスコアリングサービス
ルールベース分析結果とマルチロールLLM分析結果を統合して最終スコアを決定
"""

from typing import Any, Dict, List


class EnsembleScoringService:
    """
    ルールベース + ロール別LLM結果を統合するサービス
    
    - ルールベース結果を安全側のベースラインとして使用
    - ロール別スコアを重み付き平均で集約
    - severity / urgency は安全側（強い方を優先）で決定
    """

    # severity / urgency の優先度
    _severity_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    _urgency_order = ["LOW", "MEDIUM", "HIGH", "URGENT", "IMMEDIATE"]

    def combine(
        self,
        rule_result: Dict[str, Any],
        role_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        アンサンブル結果を計算
        
        Args:
            rule_result: StructureAnalyzer._analyze_with_rules の結果
            role_results: MultiRoleLLMAnalyzer.analyze_with_roles の結果
        """
        base_score = rule_result.get("overall_score", 0)
        base_severity = rule_result.get("severity", "LOW")
        base_urgency = rule_result.get("urgency", "LOW")

        if not role_results:
            # LLMが使えない場合はルールベースのみ
            return {
                "overall_score": base_score,
                "severity": base_severity,
                "urgency": base_urgency,
                "reasons": [rule_result.get("explanation", "")],
                "contributing_roles": [],
                "findings": rule_result.get("findings", []),
                "explanation": rule_result.get("explanation", ""),
            }

        # ロール別スコアを重み付きで集約
        total_weight = sum(r.get("weight", 0.0) for r in role_results) or 1.0
        llm_score = sum(
            (r.get("overall_score", 0) * r.get("weight", 0.0)) for r in role_results
        ) / total_weight

        # ルール: ルールベース6割 + LLM4割（プラン記述通り）
        overall_score = int(0.6 * base_score + 0.4 * llm_score)

        # severity / urgency を安全側で決定
        role_severities = [r.get("severity", "LOW") for r in role_results]
        role_urgencies = [r.get("urgency", "LOW") for r in role_results]

        severity = self._max_level([base_severity] + role_severities, self._severity_order)
        urgency = self._max_level([base_urgency] + role_urgencies, self._urgency_order)

        # 説明文: ルールベースの説明 + 主要ロール（executive, corp_planning）のコメント
        reasons: List[str] = []
        base_explanation = rule_result.get("explanation")
        if base_explanation:
            reasons.append(base_explanation)

        # 代表ロールのコメントを簡潔に追加
        for r in role_results:
            role_id = r.get("role_id")
            if role_id in {"executive", "corp_planning"}:
                exp = r.get("explanation")
                if exp:
                    reasons.append(f"[{role_id}] {exp}")

        explanation = " ".join(reasons) if reasons else rule_result.get("explanation", "")

        contributing_roles = [
            {
                "role_id": r.get("role_id"),
                "weight": r.get("weight"),
                "overall_score": r.get("overall_score"),
                "severity": r.get("severity"),
                "urgency": r.get("urgency"),
            }
            for r in role_results
        ]

        return {
            "overall_score": overall_score,
            "severity": severity,
            "urgency": urgency,
            "reasons": reasons,
            "contributing_roles": contributing_roles,
            # ルールベースのfindingをそのまま採用（将来的にロール別マージも検討）
            "findings": rule_result.get("findings", []),
            "explanation": explanation,
        }

    @staticmethod
    def _max_level(values: List[str], order: List[str]) -> str:
        """優先度リストに基づいて最大レベルを返す"""
        rank = {name: i for i, name in enumerate(order)}
        return max(values, key=lambda v: rank.get(v, 0))

