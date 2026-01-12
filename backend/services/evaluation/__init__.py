"""
評価構造の設計
LLMレスポンスの評価構造を定義し、パースしやすくする
"""

from .schema import (
    AnalysisFinding,
    AnalysisResult,
    TaskDefinition,
    TaskGenerationResult
)
from .parser import EvaluationParser

__all__ = [
    "AnalysisFinding",
    "AnalysisResult",
    "TaskDefinition",
    "TaskGenerationResult",
    "EvaluationParser",
]
