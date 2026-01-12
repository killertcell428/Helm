"""
出力ファイル生成サービス
LLM生成結果をJSON形式でファイルに出力し、ダウンロード可能にする
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from utils.logger import logger


class OutputService:
    """出力サービス"""
    
    def __init__(self, output_dir: str = "outputs"):
        """
        Args:
            output_dir: 出力ディレクトリのパス
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"Output service initialized: output_dir={self.output_dir.absolute()}")
    
    def save_analysis_result(self, analysis_id: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析結果をJSON形式で保存
        
        Args:
            analysis_id: 分析ID
            analysis_result: 分析結果
            
        Returns:
            保存されたファイル情報
        """
        filename = f"analysis_{analysis_id}.json"
        filepath = self.output_dir / filename
        
        # メタデータを追加
        output_data = {
            "analysis_id": analysis_id,
            "generated_at": datetime.now().isoformat(),
            "result": analysis_result
        }
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)
            
            file_size = filepath.stat().st_size
            
            logger.info(f"Analysis result saved: {filepath} ({file_size} bytes)")
            
            return {
                "file_id": filename,
                "filepath": str(filepath),
                "filename": filename,
                "size": file_size,
                "type": "analysis",
                "created_at": output_data["generated_at"]
            }
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"Failed to save analysis result: {e}",
                extra={
                    "error_type": error_type,
                    "analysis_id": analysis_id,
                    "filepath": str(filepath)
                },
                exc_info=True
            )
            raise
    
    def save_task_generation_result(
        self,
        execution_id: str,
        task_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        タスク生成結果をJSON形式で保存
        
        Args:
            execution_id: 実行ID
            task_result: タスク生成結果
            
        Returns:
            保存されたファイル情報
        """
        filename = f"tasks_{execution_id}.json"
        filepath = self.output_dir / filename
        
        # メタデータを追加
        output_data = {
            "execution_id": execution_id,
            "generated_at": datetime.now().isoformat(),
            "result": task_result
        }
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)
            
            file_size = filepath.stat().st_size
            
            logger.info(f"Task generation result saved: {filepath} ({file_size} bytes)")
            
            return {
                "file_id": filename,
                "filepath": str(filepath),
                "filename": filename,
                "size": file_size,
                "type": "tasks",
                "created_at": output_data["generated_at"]
            }
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"Failed to save task generation result: {e}",
                extra={
                    "error_type": error_type,
                    "execution_id": execution_id,
                    "filepath": str(filepath)
                },
                exc_info=True
            )
            raise
    
    def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        ファイルを取得
        
        Args:
            file_id: ファイルID（filename）
            
        Returns:
            ファイル内容（Dict形式）、見つからない場合はNone
        """
        filepath = self.output_dir / file_id
        
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read file {filepath}: {e}", exc_info=True)
            return None
    
    def list_files(self, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        ファイル一覧を取得
        
        Args:
            file_type: ファイルタイプでフィルタ（"analysis" または "tasks"）
            
        Returns:
            ファイル情報のリスト
        """
        files = []
        
        for filepath in self.output_dir.glob("*.json"):
            try:
                stat = filepath.stat()
                file_info = {
                    "file_id": filepath.name,
                    "filename": filepath.name,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
                
                # ファイルタイプを判定
                if filepath.name.startswith("analysis_"):
                    file_info["type"] = "analysis"
                elif filepath.name.startswith("tasks_"):
                    file_info["type"] = "tasks"
                else:
                    file_info["type"] = "unknown"
                
                # フィルタリング
                if file_type and file_info["type"] != file_type:
                    continue
                
                files.append(file_info)
            except Exception as e:
                logger.warning(f"Failed to get file info for {filepath}: {e}")
                continue
        
        # 作成日時でソート（新しい順）
        files.sort(key=lambda x: x["created_at"], reverse=True)
        
        return files
    
    def get_file_path(self, file_id: str) -> Optional[Path]:
        """
        ファイルパスを取得
        
        Args:
            file_id: ファイルID（filename）
            
        Returns:
            ファイルパス、見つからない場合はNone
        """
        filepath = self.output_dir / file_id
        
        if filepath.exists():
            return filepath
        else:
            return None
