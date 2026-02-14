"""
プロンプトファイル読み込みユーティリティ
config/prompts/ 配下のテキストファイルを変数的に読み込む
組織グラフ・RACIと同様の設計思想（DefinitionLoaderと同様のパス解決）
"""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# backend/config/prompts/ のパス（services/prompts/ -> services/ -> backend/）
_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "prompts"


def _get_prompts_dir() -> Path:
    """プロンプトディレクトリの絶対パスを取得"""
    return _PROMPTS_DIR


def load_prompt(relative_path: str, fallback: Optional[str] = None) -> str:
    """
    プロンプトファイルを読み込む
    
    Args:
        relative_path: config/prompts/ からの相対パス（例: "analysis/base.txt"）
        fallback: ファイルが存在しない場合のフォールバック文字列
        
    Returns:
        プロンプト文字列。ファイルが存在しない場合はfallback、fallbackもNoneなら空文字
    """
    file_path = _get_prompts_dir() / relative_path
    try:
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            return content.strip()
    except Exception as e:
        logger.warning(f"プロンプトファイル読み込み失敗: {relative_path}, error={e}")
    
    if fallback is not None:
        return fallback
    return ""


def load_analysis_prompt(role_id: str, prompt_type: str) -> Optional[str]:
    """
    分析用プロンプトを読み込む
    
    Args:
        role_id: executive, staff, corp_planning, governance, default
        prompt_type: role_description または analysis_points
        
    Returns:
        読み込んだ文字列。存在しない場合はNone（呼び出し側でフォールバック）
    """
    if prompt_type == "role_description":
        filename = f"role_{role_id}.txt" if role_id != "default" else "role_default.txt"
    elif prompt_type == "analysis_points":
        filename = f"analysis_points_{role_id}.txt" if role_id != "default" else "analysis_points_default.txt"
    else:
        return None
    
    path = f"analysis/{filename}"
    content = load_prompt(path)
    return content if content else None


def load_task_generation_template() -> Optional[str]:
    """タスク生成用プロンプトテンプレートを読み込む"""
    content = load_prompt("task_generation.txt")
    return content if content else None


def load_agent_instruction(agent_id: str) -> Optional[str]:
    """
    ADKエージェントのinstructionを読み込む
    
    Args:
        agent_id: research, analysis, notification
        
    Returns:
        読み込んだinstruction。存在しない場合はNone
    """
    filename = f"{agent_id}_instruction.txt"
    content = load_prompt(f"agents/{filename}")
    return content if content else None


def load_agent_prompt_template(agent_id: str) -> Optional[str]:
    """
    ADKエージェント実行時のuser promptテンプレートを読み込む
    
    Args:
        agent_id: research, analysis, notification
        
    Returns:
        読み込んだテンプレート（{topic}等のプレースホルダ含む）。存在しない場合はNone
    """
    filename = f"{agent_id}_prompt.txt"
    content = load_prompt(f"agents/{filename}")
    return content if content else None
