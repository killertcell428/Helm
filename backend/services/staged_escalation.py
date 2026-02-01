"""
段階的エスカレーション機能
通知→レビュー→承認依頼→強制議題化の段階設計
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
from utils.logger import logger
from utils.exceptions import ServiceError


class EscalationStage(str, Enum):
    """エスカレーション段階"""
    NOTIFICATION = "notification"  # 通知のみ
    REVIEW = "review"  # レビュー
    APPROVAL_REQUEST = "approval_request"  # 承認依頼
    FORCED_AGENDA = "forced_agenda"  # 強制議題化


class StagedEscalationEngine:
    """段階的エスカレーションエンジン"""
    
    # スコアと段階のマッピング
    STAGE_THRESHOLDS = {
        EscalationStage.NOTIFICATION: (50, 60),
        EscalationStage.REVIEW: (60, 70),
        EscalationStage.APPROVAL_REQUEST: (70, 80),
        EscalationStage.FORCED_AGENDA: (80, 100)
    }
    
    # サイレンス期間（デフォルト: 24時間）
    SILENCE_PERIOD_HOURS = 24
    
    def __init__(self, silence_period_hours: int = None):
        """
        Args:
            silence_period_hours: サイレンス期間（時間）
        """
        self.silence_period_hours = silence_period_hours or self.SILENCE_PERIOD_HOURS
        # パターンごとの最後の通知時刻を記録
        self.last_notification_times: Dict[str, datetime] = {}
    
    def determine_stage(
        self,
        analysis_result: Dict[str, Any],
        pattern_id: Optional[str] = None
    ) -> Optional[EscalationStage]:
        """
        エスカレーション段階を決定（エラーハンドリング付き）
        
        Args:
            analysis_result: 分析結果
            pattern_id: パターンID
            
        Returns:
            エスカレーション段階（エラー時はNone）
        """
        try:
            if not analysis_result or not isinstance(analysis_result, dict):
                logger.warning("Invalid analysis_result, returning None")
                return None
            
            # スコアを取得
            overall_score = analysis_result.get("overall_score", 0)
            if overall_score == 0:
                overall_score = analysis_result.get("score", 0)
            if overall_score == 0:
                ensemble = analysis_result.get("ensemble", {})
                if isinstance(ensemble, dict):
                    overall_score = ensemble.get("overall_score", 0)
            
            # スコアを数値に変換
            try:
                overall_score = int(float(overall_score))
            except (ValueError, TypeError):
                logger.warning(f"Invalid score value: {overall_score}, using 0")
                overall_score = 0
            
            # 重要度を取得
            severity = analysis_result.get("severity", "LOW")
            ensemble = analysis_result.get("ensemble", {})
            if isinstance(ensemble, dict) and (not severity or severity == "LOW"):
                severity = ensemble.get("severity", severity)
            
            if not isinstance(severity, str):
                severity = "LOW"
            
            # スコアに基づいて段階を決定
            if overall_score >= 80 or severity == "CRITICAL":
                return EscalationStage.FORCED_AGENDA
            elif overall_score >= 70 or severity == "HIGH":
                return EscalationStage.APPROVAL_REQUEST
            elif overall_score >= 60:
                return EscalationStage.REVIEW
            elif overall_score >= 50:
                return EscalationStage.NOTIFICATION
            else:
                # スコアが50未満の場合は通知しない
                return None
        except Exception as e:
            logger.error(f"Failed to determine escalation stage: {e}", exc_info=True)
            # エラー時はNoneを返す（フォールバック）
            return None
    
    def should_notify(
        self,
        stage: Optional[EscalationStage],
        pattern_id: Optional[str] = None
    ) -> bool:
        """
        通知すべきか判断（サイレンス期間を考慮、エラーハンドリング付き）
        
        Args:
            stage: エスカレーション段階
            pattern_id: パターンID
            
        Returns:
            通知すべき場合True
        """
        try:
            if stage is None:
                return False
            
            # 強制議題化の場合は常に通知
            if stage == EscalationStage.FORCED_AGENDA:
                return True
            
            # パターンIDが指定されていない場合は通知
            if not pattern_id:
                return True
            
            # サイレンス期間をチェック
            last_time = self.last_notification_times.get(pattern_id)
            if last_time is None:
                # 初回の通知
                self.last_notification_times[pattern_id] = datetime.now()
                return True
            
            # サイレンス期間が経過しているかチェック
            if isinstance(last_time, datetime):
                elapsed = datetime.now() - last_time
                if elapsed >= timedelta(hours=self.silence_period_hours):
                    # サイレンス期間が経過したので通知
                    self.last_notification_times[pattern_id] = datetime.now()
                    return True
            else:
                # 無効なタイムスタンプの場合は通知
                logger.warning(f"Invalid last_time for pattern {pattern_id}, resetting")
                self.last_notification_times[pattern_id] = datetime.now()
                return True
            
            # サイレンス期間内なので通知しない
            return False
        except Exception as e:
            logger.error(f"Failed to check notification status: {e}", exc_info=True)
            # エラー時は安全側で通知する（フォールバック）
            return True
    
    def get_stage_description(self, stage: EscalationStage) -> Dict[str, Any]:
        """
        段階の説明を取得
        
        Args:
            stage: エスカレーション段階
            
        Returns:
            段階の説明
        """
        descriptions = {
            EscalationStage.NOTIFICATION: {
                "stage": "notification",
                "name": "通知",
                "description": "構造的問題の兆候が検出されました。監視を継続します。",
                "action_required": False,
                "target_roles": ["Manager", "Staff"]
            },
            EscalationStage.REVIEW: {
                "stage": "review",
                "name": "レビュー",
                "description": "構造的問題の可能性があります。レビューをお願いします。",
                "action_required": True,
                "target_roles": ["Manager"]
            },
            EscalationStage.APPROVAL_REQUEST: {
                "stage": "approval_request",
                "name": "承認依頼",
                "description": "構造的問題が検出されました。承認をお願いします。",
                "action_required": True,
                "target_roles": ["Executive"]
            },
            EscalationStage.FORCED_AGENDA: {
                "stage": "forced_agenda",
                "name": "強制議題化",
                "description": "緊急の構造的問題が検出されました。次回会議で必ず議論してください。",
                "action_required": True,
                "target_roles": ["Executive"]
            }
        }
        
        return descriptions.get(stage, {
            "stage": "unknown",
            "name": "不明",
            "description": "",
            "action_required": False,
            "target_roles": []
        })
    
    def create_escalation_with_stage(
        self,
        analysis_id: str,
        analysis_result: Dict[str, Any],
        pattern_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        段階を考慮したエスカレーションを作成
        
        Args:
            analysis_id: 分析ID
            analysis_result: 分析結果
            pattern_id: パターンID
            
        Returns:
            エスカレーションデータ（通知しない場合はNone）
        """
        # 段階を決定
        stage = self.determine_stage(analysis_result, pattern_id)
        
        if stage is None:
            return None
        
        # 通知すべきか判断
        if not self.should_notify(stage, pattern_id):
            logger.info(f"Silence period active for pattern {pattern_id}, skipping notification")
            return None
        
        # 段階の説明を取得
        stage_info = self.get_stage_description(stage)
        
        # スコアを取得
        overall_score = analysis_result.get("overall_score", 0)
        if overall_score == 0:
            overall_score = analysis_result.get("score", 0)
        if overall_score == 0:
            ensemble = analysis_result.get("ensemble", {})
            if isinstance(ensemble, dict):
                overall_score = ensemble.get("overall_score", 0)
        
        # 重要度・緊急度を取得
        severity = analysis_result.get("severity", "MEDIUM")
        urgency = analysis_result.get("urgency", "MEDIUM")
        ensemble = analysis_result.get("ensemble", {})
        if isinstance(ensemble, dict):
            if not severity or severity == "LOW":
                severity = ensemble.get("severity", severity)
            if not urgency or urgency == "LOW":
                urgency = ensemble.get("urgency", urgency)
        
        # エスカレーション理由を生成
        reason = self._generate_reason(analysis_result, stage_info)
        
        return {
            "analysis_id": analysis_id,
            "stage": stage_info["stage"],
            "stage_name": stage_info["name"],
            "target_roles": stage_info["target_roles"],
            "reason": reason,
            "description": stage_info["description"],
            "severity": severity,
            "urgency": urgency,
            "score": overall_score,
            "action_required": stage_info["action_required"],
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
    
    def _generate_reason(
        self,
        analysis_result: Dict[str, Any],
        stage_info: Dict[str, Any]
    ) -> str:
        """
        エスカレーション理由を生成
        
        Args:
            analysis_result: 分析結果
            stage_info: 段階情報
            
        Returns:
            エスカレーション理由
        """
        findings = analysis_result.get("findings", [])
        
        if not findings:
            return f"{stage_info['description']} スコア: {analysis_result.get('overall_score', 0)}点"
        
        finding = findings[0]
        pattern_id = finding.get("pattern_id", "")
        
        reason_parts = [stage_info["description"]]
        
        # パターンに基づく説明
        if pattern_id == "B1_正当化フェーズ":
            reason_parts.append("正当化フェーズの兆候が検出されました。")
        elif pattern_id == "ES1_報告遅延":
            reason_parts.append("エスカレーション遅延が検出されました。")
        else:
            reason_parts.append("構造的問題が検出されました。")
        
        # スコアと重要度・緊急度
        overall_score = analysis_result.get("overall_score", 0)
        severity = analysis_result.get("severity", "MEDIUM")
        urgency = analysis_result.get("urgency", "MEDIUM")
        reason_parts.append(f"スコア: {overall_score}点（重要度: {severity}, 緊急度: {urgency}）")
        
        return " ".join(reason_parts)
