"""
AnalysisAgent
社内データ統合エージェント
ADK統合、モック実装、フォールバック対応
"""

from services.adk_setup import get_model, get_or_create_runner, ADK_AVAILABLE
from services.google_workspace import GoogleWorkspaceService
from typing import Dict, Any, Optional, List
import logging
import json

logger = logging.getLogger(__name__)

# モックツールの戻り値スキーマを固定（将来のAPI統合を見据える）
def fetch_internal_data(query: str) -> str:
    """Google Driveから社内データを取得（モック実装、将来はGoogle Drive API）"""
    logger.info(f"社内データ取得（モック）: {query}")
    # TODO: 実際の実装では、Google Drive APIでデータを検索・取得
    # 戻り値はJSON形式で統一（将来のAPI統合を見据える）
    result = {
        "query": query,
        "data_sources": [
            {"source": "過去の戦略変更事例", "summary": "類似プロジェクトの成功/失敗データ"},
            {"source": "社内データベース", "summary": "関連する財務データ、KPIデータ"}
        ],
        "raw": f"{query}に関する社内データ"
    }
    return json.dumps(result, ensure_ascii=False)

def perform_financial_simulation(data: str) -> str:
    """財務シミュレーションを実行（継続、縮小、撤退の3案）"""
    logger.info("財務シミュレーションを実行（モック）")
    # TODO: 実際の実装では、Geminiを使用して財務シミュレーションを実行
    # 戻り値はJSON形式で統一（将来のAPI統合を見据える）
    result = {
        "analysis_type": "financial_simulation",
        "results": {
            "継続案": {
                "expected_revenue": 1000,
                "expected_cost": 800,
                "expected_profit": 200,
                "risk_level": "medium"
            },
            "縮小案": {
                "expected_revenue": 700,
                "expected_cost": 500,
                "expected_profit": 200,
                "risk_level": "low"
            },
            "撤退案": {
                "expected_revenue": 0,
                "expected_cost": 100,
                "expected_profit": -100,
                "risk_level": "low"
            }
        }
    }
    return json.dumps(result, ensure_ascii=False)

# ツールを定義（ADKが利用可能な場合のみ）
if ADK_AVAILABLE:
    from google.adk.tools import FunctionTool
    internal_data_tool = FunctionTool(fetch_internal_data)
    financial_sim_tool = FunctionTool(perform_financial_simulation)
else:
    internal_data_tool = None
    financial_sim_tool = None

def build_analysis_agent():
    """AnalysisAgentを構築（ADKが利用可能な場合のみ、公式API準拠）"""
    if not ADK_AVAILABLE:
        return None
    
    model = get_model()
    if model is None:
        return None  # APIキー未設定時はNoneを返す
    
    from google.adk.agents.llm_agent import Agent  # or LlmAgent
    
    return Agent(
        name="analysis_agent",
        model=model,  # llm=ではなくmodel=（公式API準拠）
        description="社内データを統合・分析し、財務シミュレーションを実行するエージェント",
        instruction="""
        過去の戦略変更事例、類似プロジェクトの成功/失敗データを収集し、
        継続案、縮小案、撤退案の財務シミュレーションを実行してください。
        fetch_internal_data関数でデータを取得し、perform_financial_simulation関数で分析してください。
        結果は構造化された形式（JSON形式）で返してください。
        """,
        tools=[internal_data_tool, financial_sim_tool] if internal_data_tool else []
    )

async def execute_analysis_task(task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """AnalysisAgentを実行（ADKが利用可能な場合は使用、そうでない場合はモック）"""
    agent = build_analysis_agent()
    
    if agent is not None:
        try:
            runner_info = get_or_create_runner(agent, agent_id="analysis_agent")
            if runner_info is None:
                raise Exception("Runner creation failed")
            
            runner, session_service, app_name = runner_info
            
            # 新しいセッションを作成（実行単位ごとにセッションを作成）
            import uuid
            user_id = "helm_user"
            session_id = str(uuid.uuid4())
            await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
            
            prompt = f"社内データを統合し、財務シミュレーションを実行してください。{task.get('description', '')}"
            
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
                "is_adk_generated": True,
                "session_id": session_id
            }
        except Exception as e:
            logger.warning(f"ADK AnalysisAgent execution failed, falling back to mock: {e}", exc_info=True)
    
    # フォールバック: 既存のモック実装
    workspace_service = GoogleWorkspaceService()
    result = workspace_service.analyze_data({})
    return {
        "data": result,
        "status": "completed",
        "is_adk_generated": False
    }
