"""
ADK (Agent Development Kit) セットアップ
公式API準拠の実装
"""

from typing import Optional, Dict
import os
import logging

logger = logging.getLogger(__name__)

# ADKが利用可能かチェック（公式API準拠のimportパス）
try:
    from google.adk.agents.llm_agent import Agent  # or LlmAgent（公式ドキュメントに準拠）
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService, VertexAiSessionService
    from google.adk.models.google_llm import Gemini
    from google.adk.tools import FunctionTool
    ADK_AVAILABLE = True
except ImportError as e:
    ADK_AVAILABLE = False
    logger.warning(f"ADK is not installed. Mock mode will be used. Error: {e}")

# Runnerのシングルトン管理（Agentごとに1つのRunnerインスタンス）
# 値は (runner, session_service, app_name) のタプル
_runners: Dict[str, tuple] = {}

def get_model():
    """LLMモデルインスタンスを取得（環境変数に基づいて選択、公式API準拠）
    
    モデル名: ADK_MODEL で指定。未設定時は gemini-2.0-flash。
    gemini-1.5-flash は API v1beta で NOT_FOUND になるため、2.0 系をデフォルトにしている。
    """
    if not ADK_AVAILABLE:
        return None  # モックモード
    
    model_name = os.getenv("ADK_MODEL", "gemini-2.0-flash")
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() == "true"
    
    if use_vertex:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
        location = os.getenv("LOCATION", "us-central1")
        if project_id:
            from google.cloud import aiplatform
            aiplatform.init(project=project_id, location=location)
            return Gemini(model=model_name, vertex_ai=True)
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        return Gemini(model=model_name)
    
    return None  # APIキー未設定時はモックモード

def get_or_create_runner(agent, agent_id: str = "default") -> Optional[tuple]:
    """RunnerインスタンスとSessionServiceを取得または作成（シングルトンパターン）
    
    Returns:
        tuple: (runner, session_service, app_name) または None
    """
    if not ADK_AVAILABLE or agent is None:
        return None  # モックモード
    
    # 既存のRunnerがあれば再利用
    runner_key = f"{agent_id}_runner"
    session_key = f"{agent_id}_session"
    app_name = f"helm_{agent_id}"
    
    if runner_key in _runners:
        return _runners[runner_key]
    
    # 新しいRunnerを作成
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() == "true"
    
    if use_vertex:
        # Vertex AI使用時はAgent Engine IDが必要（Phase2でドキュメント化）
        # 現時点ではInMemorySessionServiceを使用
        session_service = InMemorySessionService()
        logger.warning("VertexAiSessionService requires Agent Engine ID. Using InMemorySessionService for now.")
    else:
        session_service = InMemorySessionService()
    
    # Runnerの初期化にはapp_nameとagentの両方が必要
    runner = Runner(app_name=app_name, agent=agent, session_service=session_service)
    
    # Runner、SessionService、app_nameをタプルで返す
    result = (runner, session_service, app_name)
    _runners[runner_key] = result
    return result

def clear_runners():
    """Runnerのキャッシュをクリア（テスト用）"""
    _runners.clear()
