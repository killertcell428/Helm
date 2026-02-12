"""
定義ドキュメントの読み込み
org_graph, raci, approval_flows をファイル（のちに Firestore 優先）から取得
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from utils.logger import logger


class DefinitionLoader:
    """3 種の定義（org_graph, raci, approval_flows）を読み返す。"""

    def __init__(self, definitions_dir: Optional[Path] = None):
        if definitions_dir is None:
            # backend/services/ -> backend/config/definitions/
            definitions_dir = Path(__file__).resolve().parent.parent / "config" / "definitions"
        self.definitions_dir = Path(definitions_dir)

    def _load_json(self, name: str) -> Optional[Dict[str, Any]]:
        path = self.definitions_dir / f"{name}.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load definition {name}: {e}")
            return None

    def get_org_graph(self) -> Optional[Dict[str, Any]]:
        return self._load_json("org_graph")

    def get_raci(self) -> Optional[Dict[str, Any]]:
        return self._load_json("raci")

    def get_approval_flows(self) -> Optional[Dict[str, Any]]:
        return self._load_json("approval_flows")
