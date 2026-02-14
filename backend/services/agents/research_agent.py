"""
ResearchAgent
市場データ分析エージェント
ADK統合、モック実装、フォールバック対応
"""

from services.adk_setup import get_model, get_or_create_runner, ADK_AVAILABLE
from services.google_workspace import GoogleWorkspaceService
from services.prompts.loader import load_agent_instruction, load_agent_prompt_template
from typing import Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)

# フォールバック用instruction（ファイル読み込み失敗時）
_RESEARCH_INSTRUCTION_FALLBACK = """
与えられたトピックについて、市場データを検索し、分析・要約を行ってください。
search_market_data関数でデータを収集し、analyze_market_data関数で分析してください。
結果は構造化された形式（JSON形式）で返してください。
"""

# モックツールの戻り値スキーマを固定（将来のAPI統合を見据える）
def search_market_data(topic: str) -> str:
    """市場データを検索する（モック実装、将来はVertex AI Search API）"""
    logger.info(f"市場データ検索（モック）: {topic}")
    # TODO: 実際の実装では、Vertex AI Search APIを呼び出す
    # 戻り値はJSON形式で統一（将来のAPI統合を見据える）
    result = {
        "topic": topic,
        "sources": [
            {"source": "業界レポート", "title": "通信業界のARPU動向", "summary": "業界平均ARPUは前年同期比▲5.1%"},
            {"source": "競合分析", "title": "主要競合他社のARPU推移", "summary": "A社: ▲3.2%, B社: ▲7.8%, C社: ▲4.5%"}
        ],
        "highlights": ["ARPU低下傾向", "競合他社も同様の傾向"],
        "raw": f"{topic}に関する市場データ"
    }
    return json.dumps(result, ensure_ascii=False)

def analyze_market_data(search_results: str) -> str:
    """検索結果を分析・要約する（モック実装）"""
    logger.info("市場データ分析を実行（モック）")
    # TODO: 実際の実装では、Geminiを使用して分析
    return f"分析結果: {search_results}を基にした要約"

# ツールを定義（ADKが利用可能な場合のみ）
if ADK_AVAILABLE:
    from google.adk.tools import FunctionTool
    market_search_tool = FunctionTool(search_market_data)
    market_analysis_tool = FunctionTool(analyze_market_data)
else:
    market_search_tool = None
    market_analysis_tool = None

def build_research_agent():
    """ResearchAgentを構築（ADKが利用可能な場合のみ、公式API準拠）"""
    if not ADK_AVAILABLE:
        return None
    
    model = get_model()
    if model is None:
        return None  # APIキー未設定時はNoneを返す
    
    from google.adk.agents.llm_agent import Agent  # or LlmAgent
    
    instruction = load_agent_instruction("research")
    if not instruction:
        instruction = _RESEARCH_INSTRUCTION_FALLBACK.strip()
    
    return Agent(
        name="research_agent",
        model=model,  # llm=ではなくmodel=（公式API準拠）
        description="市場データを収集・分析するエージェント",
        instruction=instruction,
        tools=[market_search_tool, market_analysis_tool] if market_search_tool else []
    )

async def execute_research_task(task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """ResearchAgentを実行（ADKが利用可能な場合は使用、そうでない場合はモック）"""
    agent = build_research_agent()
    
    if agent is not None:
        try:
            runner_info = get_or_create_runner(agent, agent_id="research_agent")
            if runner_info is None:
                raise Exception("Runner creation failed")
            
            runner, session_service, app_name = runner_info
            
            # 新しいセッションを作成（実行単位ごとにセッションを作成）
            import uuid
            user_id = "helm_user"
            session_id = str(uuid.uuid4())
            await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
            
            description = task.get("description", "")
            topic = description.split("：")[-1] if "：" in description else task.get("name", "")
            template = load_agent_prompt_template("research")
            prompt = template.format(topic=topic) if template else f"以下のトピックについて市場データを収集・分析してください: {topic}"
            
            # async関数内ではrun_async()を使用
            from google.genai import types
            content = types.Content(role="user", parts=[types.Part(text=prompt)])
            final_text = "No response produced."
            
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = event.content.parts[0].text
                    break
            
            return {
                "data": final_text,
                "status": "completed",
                "topic": topic,
                "is_adk_generated": True,
                "session_id": session_id
            }
        except Exception as e:
            logger.warning(f"ADK ResearchAgent execution failed, falling back to mock: {e}", exc_info=True)
    
    # フォールバック: 既存のモック実装
    workspace_service = GoogleWorkspaceService()
    result = workspace_service.research_market_data(task.get("name", "ARPU動向"))
    return {
        "data": result,
        "status": "completed",
        "is_adk_generated": False,
        "topic": task.get("name", "ARPU動向")
    }
