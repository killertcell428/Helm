"""
説明文の根拠引用機能
発話ID/タイムスタンプ付きの説明文生成
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from utils.logger import logger
from utils.exceptions import ServiceError


class EvidenceCitationService:
    """根拠引用サービス"""
    
    def __init__(self):
        """初期化"""
        pass
    
    def add_evidence_citations(
        self,
        explanation: str,
        findings: List[Dict[str, Any]],
        meeting_data: Optional[Dict[str, Any]] = None,
        chat_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        説明文に根拠引用を追加（エラーハンドリング付き）
        
        Args:
            explanation: 元の説明文
            findings: 検出結果
            meeting_data: 会議データ
            chat_data: チャットデータ
            
        Returns:
            根拠引用付きの説明文（エラー時は元の説明文を返す）
        """
        try:
            if not explanation or not isinstance(explanation, str):
                return explanation or ""
            
            if not findings or not isinstance(findings, list):
                return explanation
            
            # 各findingから証拠を抽出
            evidence_list = []
            for finding in findings:
                try:
                    if not isinstance(finding, dict):
                        continue
                    
                    evidence = finding.get("evidence", [])
                    pattern_id = finding.get("pattern_id", "")
                    
                    # 証拠から発話IDとタイムスタンプを抽出
                    cited_evidence = self._extract_evidence_citations(
                        evidence if isinstance(evidence, list) else [],
                        meeting_data,
                        chat_data,
                        pattern_id
                    )
                    
                    if cited_evidence:
                        evidence_list.extend(cited_evidence)
                except Exception as e:
                    logger.warning(f"Failed to extract evidence from finding: {e}")
                    continue
            
            # 説明文に根拠引用を追加
            if evidence_list:
                try:
                    citation_text = self._format_citations(evidence_list)
                    return f"{explanation}\n\n【根拠】\n{citation_text}"
                except Exception as e:
                    logger.warning(f"Failed to format citations: {e}")
                    return explanation
            
            return explanation
        except Exception as e:
            logger.error(f"Failed to add evidence citations: {e}", exc_info=True)
            # エラー時は元の説明文を返す（フォールバック）
            return explanation or ""
    
    def _extract_evidence_citations(
        self,
        evidence: List[str],
        meeting_data: Optional[Dict[str, Any]],
        chat_data: Optional[Dict[str, Any]],
        pattern_id: str
    ) -> List[Dict[str, Any]]:
        """
        証拠から引用情報を抽出
        
        Args:
            evidence: 証拠リスト
            meeting_data: 会議データ
            chat_data: チャットデータ
            pattern_id: パターンID
            
        Returns:
            引用情報のリスト
        """
        citations = []
        
        # 会議データから発言を検索
        if meeting_data:
            transcript = meeting_data.get("transcript", "")
            if transcript:
                # 発言を分割（簡易版、実際はより詳細なパースが必要）
                statements = self._parse_transcript(transcript)
                for i, statement in enumerate(statements):
                    # 証拠に含まれる発言を検索
                    for ev in evidence:
                        if ev in statement.get("text", ""):
                            citations.append({
                                "type": "meeting",
                                "statement_id": f"M{i:03d}",
                                "text": statement.get("text", "")[:100],  # 最初の100文字
                                "timestamp": statement.get("timestamp"),
                                "speaker": statement.get("speaker", "不明")
                            })
        
        # チャットデータからメッセージを検索
        if chat_data:
            messages = chat_data.get("messages", [])
            for i, message in enumerate(messages):
                text = message.get("text", "")
                # 証拠に含まれるメッセージを検索
                for ev in evidence:
                    if ev in text:
                        citations.append({
                            "type": "chat",
                            "message_id": f"C{i:03d}",
                            "text": text[:100],  # 最初の100文字
                            "timestamp": message.get("timestamp"),
                            "user": message.get("user", "不明")
                        })
        
        return citations
    
    def _parse_transcript(self, transcript: str) -> List[Dict[str, Any]]:
        """
        議事録をパース（簡易版）
        
        Args:
            transcript: 議事録テキスト
            
        Returns:
            発言のリスト
        """
        statements = []
        lines = transcript.split("\n")
        
        for i, line in enumerate(lines):
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    speaker = parts[0].strip()
                    text = parts[1].strip()
                    statements.append({
                        "statement_id": f"M{i:03d}",
                        "speaker": speaker,
                        "text": text,
                        "timestamp": None  # 実際の実装ではタイムスタンプを抽出
                    })
        
        return statements
    
    def _format_citations(self, citations: List[Dict[str, Any]]) -> str:
        """
        引用情報をフォーマット
        
        Args:
            citations: 引用情報のリスト
            
        Returns:
            フォーマットされた引用テキスト
        """
        formatted = []
        for citation in citations:
            if citation["type"] == "meeting":
                formatted.append(
                    f"- 発言ID: {citation['statement_id']}, "
                    f"発言者: {citation['speaker']}, "
                    f"タイムスタンプ: {citation.get('timestamp', '不明')}\n"
                    f"  「{citation['text']}...」"
                )
            elif citation["type"] == "chat":
                formatted.append(
                    f"- メッセージID: {citation['message_id']}, "
                    f"ユーザー: {citation['user']}, "
                    f"タイムスタンプ: {citation.get('timestamp', '不明')}\n"
                    f"  「{citation['text']}...」"
                )
        
        return "\n".join(formatted)
    
    def generate_explanation_with_evidence(
        self,
        finding: Dict[str, Any],
        meeting_data: Optional[Dict[str, Any]] = None,
        chat_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        証拠付きの説明文を生成
        
        Args:
            finding: 検出結果
            meeting_data: 会議データ
            chat_data: チャットデータ
            
        Returns:
            証拠付きの説明文
        """
        pattern_id = finding.get("pattern_id", "")
        description = finding.get("description", "")
        evidence = finding.get("evidence", [])
        
        # 基本説明
        explanation = f"{description}"
        
        # 証拠引用を追加
        citations = self._extract_evidence_citations(
            evidence,
            meeting_data,
            chat_data,
            pattern_id
        )
        
        if citations:
            citation_text = self._format_citations(citations)
            explanation += f"\n\n【根拠】\n{citation_text}"
        
        return explanation
