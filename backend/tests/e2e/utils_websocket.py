"""
WebSocketユーティリティ

E2Eテストで `/api/execution/{execution_id}/ws` に対して接続し、
進捗メッセージと完了メッセージを受信するためのヘルパー。

注意:
- バックエンドサーバーが uvicorn などで起動している必要があります。
- テスト環境に `websockets` パッケージがインストールされている必要があります。
"""

import asyncio
import json
from typing import Any, Dict, List, Tuple

import websockets


BASE_WS_URL = "ws://localhost:8000"


async def _collect_execution_messages_async(
    execution_id: str,
    timeout_seconds: int = 30,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    非同期でWebSocketに接続し、executionのprogress/completedメッセージを収集する。

    Returns:
        (progress_messages, completed_messages)
    """
    uri = f"{BASE_WS_URL}/api/execution/{execution_id}/ws"
    progress_messages: List[Dict[str, Any]] = []
    completed_messages: List[Dict[str, Any]] = []

    async def _run():
        async with websockets.connect(uri) as ws:
            while True:
                raw = await ws.recv()
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = message.get("type")
                if msg_type == "progress":
                    progress_messages.append(message)
                elif msg_type == "completed":
                    completed_messages.append(message)
                    break
                elif msg_type == "error":
                    # エラーの場合もループを抜ける
                    completed_messages.append(message)
                    break

    await asyncio.wait_for(_run(), timeout=timeout_seconds)
    return progress_messages, completed_messages


def collect_execution_messages(
    execution_id: str,
    timeout_seconds: int = 30,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    同期コンテキストから呼び出すためのラッパー。

    Args:
        execution_id: 実行ID
        timeout_seconds: タイムアウト秒数

    Returns:
        (progress_messages, completed_messages)
    """
    return asyncio.run(_collect_execution_messages_async(execution_id, timeout_seconds))

