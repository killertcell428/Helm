"""
実行管理サービス
長時間実行処理の管理とタイムアウト処理
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from utils.logger import logger
from utils.exceptions import TimeoutError
from config import config


class ExecutionManager:
    """実行管理サービス"""
    
    def __init__(self):
        """実行管理サービスの初期化"""
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_timeouts: Dict[str, datetime] = {}
    
    async def execute_with_timeout(
        self,
        task_id: str,
        coro: Callable,
        timeout_seconds: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        タイムアウト付きでタスクを実行
        
        Args:
            task_id: タスクID
            coro: 実行するコルーチン関数
            timeout_seconds: タイムアウト時間（秒、Noneの場合はデフォルト値を使用）
            *args: コルーチン関数への引数
            **kwargs: コルーチン関数へのキーワード引数
            
        Returns:
            実行結果
            
        Raises:
            TimeoutError: タイムアウト時
        """
        timeout = timeout_seconds or config.get_timeout("execution")
        logger.info(f"Starting task {task_id} with timeout {timeout}s")
        
        try:
            # タイムアウト付きで実行
            result = await asyncio.wait_for(
                coro(*args, **kwargs),
                timeout=timeout
            )
            
            logger.info(f"Task {task_id} completed successfully")
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task_id} timed out after {timeout}s")
            raise TimeoutError(
                message=f"タスクがタイムアウトしました（{timeout}秒）",
                timeout_seconds=timeout,
                details={"task_id": task_id}
            )
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            raise
    
    async def execute_task_with_progress(
        self,
        task_id: str,
        tasks: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, List[Dict[str, Any]]], None]] = None,
        timeout_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        進捗更新付きでタスクを実行
        
        Args:
            task_id: タスクID
            tasks: タスクリスト
            progress_callback: 進捗更新コールバック
            timeout_seconds: タイムアウト時間（秒）
            
        Returns:
            実行結果
        """
        timeout = timeout_seconds or config.get_timeout("execution")
        start_time = datetime.now()
        
        async def execute_tasks():
            completed_tasks = []
            for i, task in enumerate(tasks):
                try:
                    # タスク実行（モック: 実際の実装では各タスクを実行）
                    await asyncio.sleep(2)  # モック: 2秒待機
                    
                    task["status"] = "completed"
                    completed_tasks.append(task)
                    
                    # 進捗更新
                    if progress_callback:
                        progress = int((len(completed_tasks) / len(tasks)) * 100)
                        await progress_callback(progress, completed_tasks)
                    
                    logger.info(f"Task {task_id}: {task['name']} completed ({i+1}/{len(tasks)})")
                    
                except Exception as e:
                    logger.error(f"Task {task_id}: {task['name']} failed: {e}", exc_info=True)
                    task["status"] = "failed"
                    task["error"] = str(e)
                    completed_tasks.append(task)
            
            return {
                "tasks": completed_tasks,
                "status": "completed",
                "progress": 100
            }
        
        try:
            result = await self.execute_with_timeout(
                task_id,
                execute_tasks,
                timeout
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Task {task_id} completed in {elapsed:.2f}s")
            
            return result
            
        except TimeoutError:
            # タイムアウト時の処理
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.warning(f"Task {task_id} timed out after {elapsed:.2f}s")
            
            # 部分的な結果を返す
            return {
                "tasks": tasks,
                "status": "timeout",
                "progress": int((elapsed / timeout) * 100)
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """
        タスクをキャンセル
        
        Args:
            task_id: タスクID
            
        Returns:
            キャンセル成功時True
        """
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel()
            del self.running_tasks[task_id]
            logger.info(f"Task {task_id} cancelled")
            return True
        return False

