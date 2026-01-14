"""
TaskWorkflowAgent
タスクの依存関係を管理し、エージェントを実行するワークフローエージェント
ADKに依存しない実装
"""

from .research_agent import execute_research_task
from .analysis_agent import execute_analysis_task
from .notification_agent import execute_notification_task
from .shared_context import SharedContext
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class TaskWorkflowAgent:
    """タスクの依存関係を管理し、エージェントを実行するワークフローエージェント"""
    
    def __init__(self):
        self.shared_context = SharedContext()
    
    def _resolve_dependencies(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """タスクの依存関係を解析し、実行順序を決定（トポロジカルソート）"""
        task_map = {task["id"]: task for task in tasks}
        in_degree = {task["id"]: len(task.get("dependencies", [])) for task in tasks}
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        execution_order = []
        
        while queue:
            task_id = queue.pop(0)
            execution_order.append(task_map[task_id])
            
            # 依存しているタスクのin_degreeを減らす
            for task in tasks:
                if task_id in task.get("dependencies", []):
                    in_degree[task["id"]] -= 1
                    if in_degree[task["id"]] == 0:
                        queue.append(task["id"])
        
        return execution_order
    
    async def execute_workflow(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ワークフローを実行"""
        execution_order = self._resolve_dependencies(tasks)
        results = {}
        
        for task in execution_order:
            task_type = task.get("type")
            task_id = task.get("id")
            
            logger.info(f"Executing task: {task_id} ({task_type})")
            
            # タスクタイプに応じて適切なエージェントを実行
            if task_type == "research":
                result = await execute_research_task(task, self.shared_context.get_context())
            elif task_type == "analysis":
                result = await execute_analysis_task(task, self.shared_context.get_context())
            elif task_type == "notification":
                result = await execute_notification_task(task, self.shared_context.get_context())
            else:
                # document, calendarなど既存の実装を使用
                result = {"status": "skipped", "message": "既存実装を使用"}
            
            results[task_id] = result
            # 結果を共有コンテキストに保存
            self.shared_context.save_result(task_id, result)
        
        return {"results": results, "status": "completed"}
