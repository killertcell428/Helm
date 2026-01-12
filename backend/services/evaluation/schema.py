"""
評価スキーマ定義
Pydanticモデルを使用してLLMレスポンスの構造を定義
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator


class QuantitativeScores(BaseModel):
    """定量評価スコア"""
    kpi_downgrade_count: int = Field(default=0, ge=0, description="KPI下方修正回数")
    exit_discussed: bool = Field(default=False, description="撤退議論の有無")
    decision_concentration_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="判断集中率")
    ignored_opposition_count: int = Field(default=0, ge=0, description="無視された反対意見数")


class AnalysisFinding(BaseModel):
    """分析結果の個別発見"""
    pattern_id: str = Field(..., description="パターンID（例: B1_正当化フェーズ）")
    severity: str = Field(..., description="重要度（HIGH|MEDIUM|LOW）")
    score: int = Field(..., ge=0, le=100, description="スコア（0-100点）")
    description: str = Field(..., description="問題の説明")
    evidence: List[str] = Field(default_factory=list, description="証拠リスト")
    quantitative_scores: Optional[QuantitativeScores] = Field(
        default=None,
        description="定量評価スコア"
    )
    
    @validator("severity")
    def validate_severity(cls, v):
        if v not in ["HIGH", "MEDIUM", "LOW"]:
            raise ValueError("severity must be HIGH, MEDIUM, or LOW")
        return v


class AnalysisResult(BaseModel):
    """構造的問題分析結果"""
    findings: List[AnalysisFinding] = Field(..., description="検出された構造的問題")
    overall_score: int = Field(..., ge=0, le=100, description="全体スコア（0-100点）")
    severity: str = Field(..., description="全体重要度（HIGH|MEDIUM|LOW）")
    urgency: str = Field(..., description="緊急度（HIGH|MEDIUM|LOW）")
    explanation: str = Field(..., description="Executive向けの説明文")
    
    @validator("severity", "urgency")
    def validate_severity_urgency(cls, v):
        if v not in ["HIGH", "MEDIUM", "LOW"]:
            raise ValueError("must be HIGH, MEDIUM, or LOW")
        return v


class TaskDefinition(BaseModel):
    """タスク定義"""
    id: str = Field(..., description="タスクID")
    name: str = Field(..., description="タスク名")
    type: str = Field(..., description="タスクタイプ（research|analysis|document|notification|calendar）")
    description: str = Field(..., description="タスクの詳細説明")
    dependencies: List[str] = Field(default_factory=list, description="依存タスクIDのリスト")
    estimated_duration: Optional[str] = Field(default=None, description="推定所要時間")
    expected_output: Optional[str] = Field(default=None, description="期待される成果物")
    
    @validator("type")
    def validate_type(cls, v):
        valid_types = ["research", "analysis", "document", "notification", "calendar"]
        if v not in valid_types:
            raise ValueError(f"type must be one of {valid_types}")
        return v


class ExecutionPlan(BaseModel):
    """実行計画"""
    total_tasks: int = Field(..., ge=0, description="総タスク数")
    estimated_total_duration: str = Field(..., description="推定総所要時間")
    critical_path: Optional[List[str]] = Field(default=None, description="クリティカルパス（タスクIDのリスト）")


class TaskGenerationResult(BaseModel):
    """タスク生成結果"""
    tasks: List[TaskDefinition] = Field(..., description="生成されたタスクリスト")
    execution_plan: ExecutionPlan = Field(..., description="実行計画")
