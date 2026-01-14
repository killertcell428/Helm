"""
NotificationAgent
通知エージェント
ADK統合、モック実装、フォールバック対応
Phase1では送信せず、ドラフト生成のみ
"""

from services.adk_setup import get_model, get_or_create_runner, ADK_AVAILABLE
from services.google_chat import GoogleChatService
from typing import Dict, Any, Optional, List
import logging
import json

logger = logging.getLogger(__name__)

# モックツールの戻り値スキーマを固定（将来のAPI統合を見据える）
def generate_notification_message(recipients: str, document_url: str, context: str) -> str:
    """通知メッセージを生成（モック実装）"""
    logger.info(f"通知メッセージ生成（モック）: 対象者={recipients}")
    # TODO: 実際の実装では、Geminiを使用して通知メッセージを生成
    # 戻り値はJSON形式で統一（将来のAPI統合を見据える）
    result = {
        "recipients": recipients.split(",") if isinstance(recipients, str) else recipients,
        "message": f"通知メッセージ: {recipients}への通知文を生成しました（文脈: {context}）",
        "document_url": document_url,
        "status": "draft"
    }
    return json.dumps(result, ensure_ascii=False)

def send_notification(recipients: List[str], message: str) -> str:
    """通知を送信する（Phase1では送信せず、ドラフトのみ生成）"""
    logger.info(f"通知送信（Phase1: ドラフト生成のみ）: {len(recipients)}名")
    # Phase1では実際の送信は行わない
    # TODO: Phase2で実際のGoogle Chat / Gmail API呼び出しを実装
    result = {
        "recipients": recipients,
        "message": message,
        "status": "draft",
        "note": "Phase1では送信せず、ドラフトのみ生成。送信はPhase2で実装"
    }
    return json.dumps(result, ensure_ascii=False)

# ツールを定義（ADKが利用可能な場合のみ）
if ADK_AVAILABLE:
    from google.adk.tools import FunctionTool
    message_gen_tool = FunctionTool(generate_notification_message)
    send_notif_tool = FunctionTool(send_notification)
else:
    message_gen_tool = None
    send_notif_tool = None

def build_notification_agent():
    """NotificationAgentを構築（ADKが利用可能な場合のみ、公式API準拠）"""
    if not ADK_AVAILABLE:
        return None
    
    model = get_model()
    if model is None:
        return None  # APIキー未設定時はNoneを返す
    
    from google.adk.agents.llm_agent import Agent  # or LlmAgent
    
    return Agent(
        name="notification_agent",
        model=model,  # llm=ではなくmodel=（公式API準拠）
        description="関係部署への通知メッセージを生成・送信するエージェント",
        instruction="""
        通知対象者と文脈に基づいて、適切な通知メッセージを生成してください。
        generate_notification_message関数でメッセージを生成し、send_notification関数でドラフトを作成してください。
        メッセージは丁寧で明確な日本語で作成してください。
        注意: Phase1では実際の送信は行わず、ドラフトのみ生成します。
        """,
        tools=[message_gen_tool, send_notif_tool] if message_gen_tool else []
    )

async def execute_notification_task(task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """NotificationAgentを実行（ADKが利用可能な場合は使用、そうでない場合はモック）"""
    agent = build_notification_agent()
    
    if agent is not None:
        try:
            runner_info = get_or_create_runner(agent, agent_id="notification_agent")
            if runner_info is None:
                raise Exception("Runner creation failed")
            
            runner, session_service, app_name = runner_info
            
            # 新しいセッションを作成（実行単位ごとにセッションを作成）
            import uuid
            user_id = "helm_user"
            session_id = str(uuid.uuid4())
            await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
            
            # 共有コンテキストからドキュメントURLなどを取得
            document_url = context.get("document_url", "")
            # 実際はタスクやコンテキストから取得（例: ["CFO", "通信本部長", "DX本部長"]）
            recipients = ["CFO", "通信本部長", "DX本部長"]
            
            prompt = f"""
            以下の情報を基に通知ドラフトを生成してください:
            - 対象者: {', '.join(recipients)}
            - 資料URL: {document_url}
            - 文脈: {task.get('description', '')}
            注意: Phase1では実際の送信は行わず、ドラフトのみ生成してください。
            """
            
            # async関数内ではrun_async()を使用
            from google.genai import types
            content = types.Content(role="user", parts=[types.Part(text=prompt)])
            final_text = "No response produced."
            
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = event.content.parts[0].text
                    break
            
            return {
                "recipients": len(recipients),
                "status": "draft",  # Phase1では送信しない
                "message": final_text,
                "is_adk_generated": True,
                "session_id": session_id,
                "note": "Phase1では送信せず、ドラフトのみ生成"
            }
        except Exception as e:
            logger.warning(f"ADK NotificationAgent execution failed, falling back to mock: {e}", exc_info=True)
    
    # フォールバック: 既存のモック実装
    return {
        "recipients": 8,
        "status": "draft",  # Phase1では送信しない
        "is_adk_generated": False,
        "note": "Phase1では送信せず、ドラフトのみ生成"
    }
