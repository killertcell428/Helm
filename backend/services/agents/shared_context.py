"""
共有コンテキスト
エージェント間でデータを共有するためのコンテキスト管理
ADKに依存しない実装
"""

from typing import Dict, Any, Optional

class SharedContext:
    """エージェント間でデータを共有するコンテキスト"""
    
    def __init__(self):
        self._context: Dict[str, Any] = {}
        self._results: Dict[str, Any] = {}
    
    def save_result(self, task_id: str, result: Dict[str, Any]):
        """タスクの実行結果を保存"""
        self._results[task_id] = result
        
        # 結果をコンテキストに反映（例: document_urlを保存）
        if "document_id" in result:
            self._context["document_url"] = result.get("view_url") or result.get("download_url")
        if "data" in result:
            self._context[f"{task_id}_data"] = result["data"]
        if "recipients" in result:
            self._context["notification_sent"] = True
    
    def get_context(self) -> Dict[str, Any]:
        """現在のコンテキストを取得"""
        return {**self._context, "results": self._results}
    
    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """特定のタスクの結果を取得"""
        return self._results.get(task_id)
    
    def clear(self):
        """コンテキストをクリア"""
        self._context.clear()
        self._results.clear()
