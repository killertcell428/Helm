"""
評価指標の計算と管理
Precision/Recall、誤検知例の記録
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import json
from pathlib import Path
from utils.logger import logger
from utils.exceptions import ServiceError


class EvaluationMetrics:
    """評価指標の計算と管理"""
    
    def __init__(self, data_dir: str = "data/evaluation"):
        """
        Args:
            data_dir: 評価データの保存ディレクトリ
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.labels_file = self.data_dir / "labels.json"
        self.metrics_file = self.data_dir / "metrics.json"
        self.false_positives_file = self.data_dir / "false_positives.json"
        
        # メモリ内のデータ
        self.labels: List[Dict[str, Any]] = []
        self.false_positives: List[Dict[str, Any]] = []
        
        # データの読み込み
        self._load_data()
    
    def _load_data(self):
        """データの読み込み（エラーハンドリング付き）"""
        # ラベルデータの読み込み
        if self.labels_file.exists():
            try:
                with open(self.labels_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.labels = data
                    else:
                        logger.warning(f"Invalid labels file format, expected list, got {type(data)}")
                        self.labels = []
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse labels JSON: {e}, using empty list")
                self.labels = []
            except Exception as e:
                logger.warning(f"Failed to load labels: {e}, using empty list", exc_info=True)
                self.labels = []
        else:
            self.labels = []
        
        # 誤検知例の読み込み
        if self.false_positives_file.exists():
            try:
                with open(self.false_positives_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.false_positives = data
                    else:
                        logger.warning(f"Invalid false positives file format, expected list, got {type(data)}")
                        self.false_positives = []
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse false positives JSON: {e}, using empty list")
                self.false_positives = []
            except Exception as e:
                logger.warning(f"Failed to load false positives: {e}, using empty list", exc_info=True)
                self.false_positives = []
        else:
            self.false_positives = []
    
    def _save_data(self):
        """データの保存（エラーハンドリング付き）"""
        # ラベルデータの保存
        try:
            # ディレクトリが存在することを確認
            self.labels_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.labels_file, "w", encoding="utf-8") as f:
                json.dump(self.labels, f, ensure_ascii=False, indent=2)
        except PermissionError as e:
            logger.error(f"Permission denied when saving labels: {e}", exc_info=True)
        except OSError as e:
            logger.error(f"OS error when saving labels: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to save labels: {e}", exc_info=True)
        
        # 誤検知例の保存
        try:
            # ディレクトリが存在することを確認
            self.false_positives_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.false_positives_file, "w", encoding="utf-8") as f:
                json.dump(self.false_positives, f, ensure_ascii=False, indent=2)
        except PermissionError as e:
            logger.error(f"Permission denied when saving false positives: {e}", exc_info=True)
        except OSError as e:
            logger.error(f"OS error when saving false positives: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to save false positives: {e}", exc_info=True)
    
    def add_label(
        self,
        meeting_id: str,
        chat_id: Optional[str],
        pattern_id: str,
        is_structural_issue: bool,
        notes: Optional[str] = None
    ) -> str:
        """
        ラベルを追加（エラーハンドリング付き）
        
        Args:
            meeting_id: 会議ID
            chat_id: チャットID（オプション）
            pattern_id: パターンID
            is_structural_issue: 構造的問題があるかどうか
            notes: 備考
            
        Returns:
            ラベルID
        """
        try:
            # 入力バリデーション
            if not meeting_id or not isinstance(meeting_id, str):
                raise ValueError("meeting_id must be a non-empty string")
            if not pattern_id or not isinstance(pattern_id, str):
                raise ValueError("pattern_id must be a non-empty string")
            if not isinstance(is_structural_issue, bool):
                raise ValueError("is_structural_issue must be a boolean")
            
            label_id = str(len(self.labels))
            label = {
                "label_id": label_id,
                "meeting_id": meeting_id,
                "chat_id": chat_id,
                "pattern_id": pattern_id,
                "is_structural_issue": is_structural_issue,
                "notes": notes,
                "created_at": datetime.now().isoformat()
            }
            self.labels.append(label)
            self._save_data()
            return label_id
        except Exception as e:
            logger.error(f"Failed to add label: {e}", exc_info=True)
            raise ServiceError(
                message=f"ラベルの追加に失敗しました: {str(e)}",
                service_name="EvaluationMetrics",
                details={"meeting_id": meeting_id, "pattern_id": pattern_id}
            )
    
    def add_false_positive(
        self,
        analysis_id: str,
        pattern_id: str,
        reason: str,
        mitigation: Optional[str] = None
    ) -> str:
        """
        誤検知例を追加
        
        Args:
            analysis_id: 分析ID
            pattern_id: パターンID
            reason: 誤検知の理由
            mitigation: 対策
            
        Returns:
            誤検知ID
        """
        fp_id = str(len(self.false_positives))
        fp = {
            "false_positive_id": fp_id,
            "analysis_id": analysis_id,
            "pattern_id": pattern_id,
            "reason": reason,
            "mitigation": mitigation,
            "created_at": datetime.now().isoformat()
        }
        self.false_positives.append(fp)
        self._save_data()
        return fp_id
    
    def calculate_metrics(self, pattern_id: Optional[str] = None) -> Dict[str, Any]:
        """
        評価指標を計算（エラーハンドリング付き）
        
        Args:
            pattern_id: パターンID（指定した場合、そのパターンのみ計算）
            
        Returns:
            評価指標（Precision、Recall、F1スコア、誤検知率）
        """
        try:
            if not self.labels:
                return {
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0,
                    "false_positive_rate": 0.0,
                    "total_labels": 0,
                    "pattern_id": pattern_id
                }
            
            # パターンIDでフィルタリング
            filtered_labels = self.labels
            if pattern_id:
                filtered_labels = [l for l in self.labels if l.get("pattern_id") == pattern_id]
            
            if not filtered_labels:
                return {
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0,
                    "false_positive_rate": 0.0,
                    "total_labels": 0,
                    "pattern_id": pattern_id
                }
            
            # True Positive, False Positive, False Negative を計算
            # 注: 実際の実装では、分析結果とラベルを比較する必要がある
            # ここでは簡易的な実装
            
            tp = sum(1 for l in filtered_labels if l.get("is_structural_issue", False))
            fp = sum(1 for l in filtered_labels if not l.get("is_structural_issue", False))
            fn = 0  # 実際の実装では、検出されなかった問題をカウント
            
            # Precision = TP / (TP + FP)
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            
            # Recall = TP / (TP + FN)
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            
            # F1スコア = 2 * (Precision * Recall) / (Precision + Recall)
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            # 誤検知率 = FP / (TP + FP)
            false_positive_rate = fp / (tp + fp) if (tp + fp) > 0 else 0.0
            
            return {
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
                "false_positive_rate": false_positive_rate,
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "total_labels": len(filtered_labels),
                "pattern_id": pattern_id
            }
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}", exc_info=True)
            # エラー時はデフォルト値を返す（フォールバック）
            return {
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "false_positive_rate": 0.0,
                "total_labels": 0,
                "pattern_id": pattern_id,
                "error": str(e)
            }
    
    def get_false_positives(self, pattern_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        誤検知例を取得
        
        Args:
            pattern_id: パターンID（指定した場合、そのパターンのみ）
            limit: 取得件数
            
        Returns:
            誤検知例のリスト
        """
        filtered = self.false_positives
        if pattern_id:
            filtered = [fp for fp in self.false_positives if fp.get("pattern_id") == pattern_id]
        
        return filtered[:limit]
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        全パターンの評価指標を取得
        
        Returns:
            パターンIDごとの評価指標
        """
        # パターンIDのリストを取得
        pattern_ids = set(l.get("pattern_id") for l in self.labels if l.get("pattern_id"))
        
        metrics_by_pattern = {}
        for pattern_id in pattern_ids:
            metrics_by_pattern[pattern_id] = self.calculate_metrics(pattern_id)
        
        # 全体の評価指標
        overall_metrics = self.calculate_metrics()
        
        return {
            "overall": overall_metrics,
            "by_pattern": metrics_by_pattern,
            "total_labels": len(self.labels),
            "total_false_positives": len(self.false_positives)
        }
