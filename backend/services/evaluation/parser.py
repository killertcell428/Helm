"""
LLMレスポンスのパース
JSONレスポンスをパースしてバリデーション
"""

import json
import re
from typing import Dict, Any, Optional
from utils.logger import logger
from .schema import AnalysisResult, TaskGenerationResult


class EvaluationParser:
    """評価結果パーサー"""
    
    @staticmethod
    def parse_analysis_response(response_text: str) -> Optional[Dict[str, Any]]:
        """
        分析結果のレスポンスをパース
        
        Args:
            response_text: LLMからのレスポンステキスト
            
        Returns:
            パースされた分析結果（Dict形式）、パース失敗時はNone
        """
        try:
            # JSONを抽出（マークダウンコードブロック内のJSONも対応）
            json_text = EvaluationParser._extract_json(response_text)
            
            if not json_text:
                logger.warning("JSON not found in response text")
                return None
            
            # JSONをパース
            parsed_data = json.loads(json_text)
            
            # Pydanticモデルでバリデーション
            analysis_result = AnalysisResult(**parsed_data)
            
            # Dict形式に変換
            return analysis_result.dict()
            
        except json.JSONDecodeError as e:
            logger.error(
                f"JSON parse error in analysis response: {e}",
                extra={
                    "error_type": "JSONDecodeError",
                    "response_preview": response_text[:200] if response_text else None
                },
                exc_info=True
            )
            return None
        except ValueError as e:
            # Pydanticバリデーションエラー
            logger.error(
                f"Validation error in analysis response: {e}",
                extra={
                    "error_type": "ValidationError",
                    "response_preview": response_text[:200] if response_text else None
                },
                exc_info=True
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error parsing analysis response: {e}",
                extra={
                    "error_type": type(e).__name__,
                    "response_preview": response_text[:200] if response_text else None
                },
                exc_info=True
            )
            return None
    
    @staticmethod
    def parse_task_generation_response(response_text: str) -> Optional[Dict[str, Any]]:
        """
        タスク生成結果のレスポンスをパース
        
        Args:
            response_text: LLMからのレスポンステキスト
            
        Returns:
            パースされたタスク生成結果（Dict形式）、パース失敗時はNone
        """
        try:
            # JSONを抽出（マークダウンコードブロック内のJSONも対応）
            json_text = EvaluationParser._extract_json(response_text)
            
            if not json_text:
                logger.warning("JSON not found in response text")
                return None
            
            # JSONをパース
            parsed_data = json.loads(json_text)
            
            # Pydanticモデルでバリデーション
            task_result = TaskGenerationResult(**parsed_data)
            
            # Dict形式に変換
            return task_result.dict()
            
        except json.JSONDecodeError as e:
            logger.error(
                f"JSON parse error in task generation response: {e}",
                extra={
                    "error_type": "JSONDecodeError",
                    "response_preview": response_text[:200] if response_text else None
                },
                exc_info=True
            )
            return None
        except ValueError as e:
            # Pydanticバリデーションエラー
            logger.error(
                f"Validation error in task generation response: {e}",
                extra={
                    "error_type": "ValidationError",
                    "response_preview": response_text[:200] if response_text else None
                },
                exc_info=True
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error parsing task generation response: {e}",
                extra={
                    "error_type": type(e).__name__,
                    "response_preview": response_text[:200] if response_text else None
                },
                exc_info=True
            )
            return None
    
    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        """
        テキストからJSONを抽出
        
        Args:
            text: 抽出元のテキスト
            
        Returns:
            抽出されたJSON文字列、見つからない場合はNone
        """
        # マークダウンコードブロック内のJSONを検索
        code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        match = re.search(code_block_pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        
        # JSONオブジェクトを直接検索
        json_pattern = r"\{.*\}"
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            return match.group(0)
        
        # 全体がJSONの可能性
        text_stripped = text.strip()
        if text_stripped.startswith("{") and text_stripped.endswith("}"):
            return text_stripped
        
        return None
    
    @staticmethod
    def validate_analysis_result(data: Dict[str, Any]) -> bool:
        """
        分析結果のバリデーション
        
        Args:
            data: バリデーション対象のデータ
            
        Returns:
            バリデーション成功時True
        """
        try:
            AnalysisResult(**data)
            return True
        except Exception as e:
            logger.warning(f"Analysis result validation failed: {e}")
            return False
    
    @staticmethod
    def validate_task_generation_result(data: Dict[str, Any]) -> bool:
        """
        タスク生成結果のバリデーション
        
        Args:
            data: バリデーション対象のデータ
            
        Returns:
            バリデーション成功時True
        """
        try:
            TaskGenerationResult(**data)
            return True
        except Exception as e:
            logger.warning(f"Task generation result validation failed: {e}")
            return False
