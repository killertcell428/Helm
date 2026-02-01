"""
エスカレーション判断エンジン（拡張版）
段階的エスカレーション、確信度に基づくエスカレーション、根拠引用を統合
既存のEscalationEngineとの互換性を保ちつつ、新機能を追加
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os
from utils.logger import logger
from utils.exceptions import ServiceError

# 新機能のインポート（エラーハンドリング付き）
try:
    from .staged_escalation import StagedEscalationEngine, EscalationStage
    STAGED_ESCALATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"StagedEscalationEngine not available: {e}")
    STAGED_ESCALATION_AVAILABLE = False
    EscalationStage = None

try:
    from .confidence_based_escalation import ConfidenceBasedEscalation, ConfidenceLevel
    CONFIDENCE_ESCALATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ConfidenceBasedEscalation not available: {e}")
    CONFIDENCE_ESCALATION_AVAILABLE = False
    ConfidenceLevel = None

try:
    from .evidence_citation import EvidenceCitationService
    EVIDENCE_CITATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"EvidenceCitationService not available: {e}")
    EVIDENCE_CITATION_AVAILABLE = False

# 既存のEscalationEngineをインポート（フォールバック用）
try:
    from .escalation_engine import EscalationEngine
    LEGACY_ESCALATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Legacy EscalationEngine not available: {e}")
    LEGACY_ESCALATION_AVAILABLE = False


class EnhancedEscalationEngine:
    """拡張エスカレーションエンジン（既存機能との互換性を保つ）"""
    
    def __init__(self, escalation_threshold: int = 50, use_enhanced_features: bool = True):
        """
        Args:
            escalation_threshold: エスカレーション閾値（スコア）
            use_enhanced_features: 拡張機能を使用するか（Falseの場合は既存機能のみ）
        """
        self.escalation_threshold = escalation_threshold
        self.use_enhanced_features = use_enhanced_features
        self.demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
        
        # 既存のエスカレーションエンジン（フォールバック用）
        if LEGACY_ESCALATION_AVAILABLE:
            self.legacy_engine = EscalationEngine(escalation_threshold=escalation_threshold)
        else:
            self.legacy_engine = None
        
        # 新機能の初期化（エラーハンドリング付き）
        self.staged_engine = None
        self.confidence_engine = None
        self.evidence_service = None
        
        if use_enhanced_features:
            try:
                if STAGED_ESCALATION_AVAILABLE:
                    self.staged_engine = StagedEscalationEngine()
                    logger.info("StagedEscalationEngine initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize StagedEscalationEngine: {e}, using legacy engine")
            
            try:
                if CONFIDENCE_ESCALATION_AVAILABLE:
                    self.confidence_engine = ConfidenceBasedEscalation()
                    logger.info("ConfidenceBasedEscalation initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize ConfidenceBasedEscalation: {e}")
            
            try:
                if EVIDENCE_CITATION_AVAILABLE:
                    self.evidence_service = EvidenceCitationService()
                    logger.info("EvidenceCitationService initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize EvidenceCitationService: {e}")
    
    def should_escalate(self, analysis_result: Dict[str, Any]) -> bool:
        """
        エスカレーションが必要か判断（既存機能との互換性を保つ）
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            エスカレーションが必要な場合True
        """
        try:
            # 既存のエンジンを使用（フォールバック）
            if self.legacy_engine:
                return self.legacy_engine.should_escalate(analysis_result)
            
            # フォールバック: 基本的な判定
            overall_score = analysis_result.get("overall_score", 0)
            if overall_score == 0:
                overall_score = analysis_result.get("score", 0)
            if overall_score == 0:
                ensemble = analysis_result.get("ensemble", {})
                if isinstance(ensemble, dict):
                    overall_score = ensemble.get("overall_score", 0)
            
            severity = analysis_result.get("severity", "LOW")
            if not severity or severity == "LOW":
                ensemble = analysis_result.get("ensemble", {})
                if isinstance(ensemble, dict):
                    severity = ensemble.get("severity", severity)
            
            if overall_score >= self.escalation_threshold:
                return True
            if severity == "HIGH" or severity == "CRITICAL":
                return True
            
            # デモ用
            if self.demo_mode:
                findings = analysis_result.get("findings", [])
                if findings and len(findings) > 0:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to check escalation: {e}", exc_info=True)
            # エラー時は安全側でTrueを返す（フォールバック）
            return True
    
    def create_escalation(
        self,
        analysis_id: str,
        analysis_result: Dict[str, Any],
        meeting_data: Optional[Dict[str, Any]] = None,
        chat_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        エスカレーションを作成（拡張機能を統合）
        
        Args:
            analysis_id: 分析ID
            analysis_result: 分析結果
            meeting_data: 会議データ（根拠引用用）
            chat_data: チャットデータ（根拠引用用）
            
        Returns:
            エスカレーションデータ（エラー時は既存機能で生成）
        """
        try:
            # 拡張機能を使用する場合
            if self.use_enhanced_features and self.staged_engine:
                try:
                    # パターンIDを取得
                    findings = analysis_result.get("findings", [])
                    pattern_id = findings[0].get("pattern_id") if findings else None
                    
                    # 段階的エスカレーションを作成
                    escalation_data = self.staged_engine.create_escalation_with_stage(
                        analysis_id,
                        analysis_result,
                        pattern_id
                    )
                    
                    if escalation_data:
                        # 根拠引用を追加
                        if self.evidence_service and meeting_data and chat_data:
                            try:
                                reason = escalation_data.get("reason", "")
                                if reason and findings:
                                    reason_with_evidence = self.evidence_service.add_evidence_citations(
                                        reason,
                                        findings,
                                        meeting_data,
                                        chat_data
                                    )
                                    escalation_data["reason"] = reason_with_evidence
                            except Exception as e:
                                logger.warning(f"Failed to add evidence citations: {e}")
                                # エラー時は根拠引用なしで続行
                        
                        # 確信度情報を追加
                        if self.confidence_engine:
                            try:
                                confidence = self.confidence_engine.calculate_confidence(analysis_result)
                                confidence_level = self.confidence_engine.get_confidence_level(confidence)
                                escalation_data["confidence"] = confidence
                                escalation_data["confidence_level"] = confidence_level.value
                                
                                # 低確信度の場合は質問として扱う
                                if self.confidence_engine.should_ask_question(analysis_result):
                                    question_data = self.confidence_engine.generate_question(analysis_result)
                                    escalation_data["question"] = question_data
                                    escalation_data["type"] = "question"
                            except Exception as e:
                                logger.warning(f"Failed to calculate confidence: {e}")
                                # エラー時は確信度情報なしで続行
                        
                        return escalation_data
                except Exception as e:
                    logger.warning(f"Failed to create staged escalation: {e}, falling back to legacy engine")
                    # フォールバック: 既存のエンジンを使用
            
            # 既存のエンジンを使用（フォールバック）
            if self.legacy_engine:
                try:
                    return self.legacy_engine.create_escalation(analysis_id, analysis_result)
                except Exception as e:
                    logger.error(f"Failed to create escalation with legacy engine: {e}", exc_info=True)
            
            # 最終フォールバック: 基本的なエスカレーションデータを生成
            return self._create_basic_escalation(analysis_id, analysis_result)
            
        except Exception as e:
            logger.error(f"Failed to create escalation: {e}", exc_info=True)
            # エラー時は基本的なエスカレーションデータを返す
            return self._create_basic_escalation(analysis_id, analysis_result)
    
    def _create_basic_escalation(
        self,
        analysis_id: str,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        基本的なエスカレーションデータを生成（フォールバック用）
        
        Args:
            analysis_id: 分析ID
            analysis_result: 分析結果
            
        Returns:
            基本的なエスカレーションデータ
        """
        try:
            overall_score = analysis_result.get("overall_score", 0)
            if overall_score == 0:
                overall_score = analysis_result.get("score", 0)
            if overall_score == 0:
                ensemble = analysis_result.get("ensemble", {})
                if isinstance(ensemble, dict):
                    overall_score = ensemble.get("overall_score", 0)
            
            severity = analysis_result.get("severity", "MEDIUM")
            urgency = analysis_result.get("urgency", "MEDIUM")
            ensemble = analysis_result.get("ensemble", {})
            if isinstance(ensemble, dict):
                if not severity or severity == "LOW":
                    severity = ensemble.get("severity", severity)
                if not urgency or urgency == "LOW":
                    urgency = ensemble.get("urgency", urgency)
            
            findings = analysis_result.get("findings", [])
            reason = "構造的問題が検出されました。"
            if findings:
                finding = findings[0]
                pattern_id = finding.get("pattern_id", "")
                if pattern_id == "B1_正当化フェーズ":
                    reason = "正当化フェーズの兆候が検出されました。"
                elif pattern_id == "ES1_報告遅延":
                    reason = "エスカレーション遅延が検出されました。"
            
            return {
                "analysis_id": analysis_id,
                "target_role": "Executive",
                "reason": reason,
                "severity": severity,
                "urgency": urgency,
                "score": overall_score,
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
        except Exception as e:
            logger.error(f"Failed to create basic escalation: {e}", exc_info=True)
            # 最終フォールバック: 最小限のデータを返す
            return {
                "analysis_id": analysis_id,
                "target_role": "Executive",
                "reason": "構造的問題が検出されました。",
                "severity": "MEDIUM",
                "urgency": "MEDIUM",
                "score": 0,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "error": "エスカレーション生成中にエラーが発生しました"
            }
    
    def determine_target_role(self, analysis_result: Dict[str, Any]) -> str:
        """
        エスカレーション先のロールを決定（既存機能との互換性を保つ）
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            ターゲットロール
        """
        try:
            if self.legacy_engine:
                return self.legacy_engine.determine_target_role(analysis_result)
            
            # フォールバック: 常にExecutive
            return "Executive"
        except Exception as e:
            logger.error(f"Failed to determine target role: {e}", exc_info=True)
            # エラー時はExecutiveを返す（フォールバック）
            return "Executive"
    
    def generate_escalation_reason(self, analysis_result: Dict[str, Any]) -> str:
        """
        エスカレーション理由を生成（既存機能との互換性を保つ）
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            エスカレーション理由
        """
        try:
            if self.legacy_engine:
                return self.legacy_engine.generate_escalation_reason(analysis_result)
            
            # フォールバック: 基本的な理由を生成
            findings = analysis_result.get("findings", [])
            if findings:
                finding = findings[0]
                pattern_id = finding.get("pattern_id", "")
                if pattern_id == "B1_正当化フェーズ":
                    return "正当化フェーズの兆候が検出されました。"
                elif pattern_id == "ES1_報告遅延":
                    return "エスカレーション遅延が検出されました。"
            
            return "構造的問題が検出されました。"
        except Exception as e:
            logger.error(f"Failed to generate escalation reason: {e}", exc_info=True)
            # エラー時は基本的な理由を返す（フォールバック）
            return "構造的問題が検出されました。"
