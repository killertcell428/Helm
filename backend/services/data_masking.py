"""
データマスキング機能
個人名、センシティブ情報のマスキング
"""

import re
from typing import Dict, List, Any, Optional
from utils.logger import logger
from utils.exceptions import ServiceError


class DataMaskingService:
    """データマスキングサービス"""
    
    # 個人名のパターン（簡易版、実際はNERを使用）
    PERSON_NAME_PATTERN = re.compile(r'[A-Z][a-z]+ [A-Z][a-z]+')  # 英語名のパターン
    
    # センシティブキーワード
    SENSITIVE_KEYWORDS = [
        r'\d+億円',
        r'\d+万円',
        r'[A-Z]社',
        r'プロジェクト[A-Z]',
        r'顧客名',
        r'取引先名'
    ]
    
    # 役職マッピング（個人名→役職）
    role_mapping: Dict[str, str] = {}
    
    def __init__(self):
        """初期化"""
        # 役職マッピングは実際の実装では外部設定ファイルから読み込む
        pass
    
    def mask_personal_names(self, text: str, meeting_data: Optional[Dict[str, Any]] = None) -> str:
        """
        個人名をマスキング（エラーハンドリング付き）
        
        Args:
            text: マスキング対象のテキスト
            meeting_data: 会議データ（参加者リストなど）
            
        Returns:
            マスキング後のテキスト（エラー時は元のテキストを返す）
        """
        try:
            if not text or not isinstance(text, str):
                return text or ""
            
            masked_text = text
            
            # 会議データから参加者リストを取得
            if meeting_data and isinstance(meeting_data, dict):
                participants = meeting_data.get("participants", [])
                if isinstance(participants, list):
                    for participant in participants:
                        try:
                            # 個人名を役職名に置換
                            if isinstance(participant, dict):
                                name = participant.get("name", "")
                                role = participant.get("role", "参加者")
                            else:
                                name = str(participant)
                                role = self._infer_role(name)
                            
                            if name and isinstance(name, str):
                                # 個人名を役職名に置換
                                masked_text = masked_text.replace(name, role)
                        except Exception as e:
                            logger.warning(f"Failed to mask participant {participant}: {e}")
                            continue
            
            # パターンマッチングで個人名を検出（簡易版）
            # 実際の実装ではNERを使用
            try:
                matches = self.PERSON_NAME_PATTERN.findall(masked_text)
                for match in matches:
                    try:
                        role = self._infer_role(match)
                        masked_text = masked_text.replace(match, role)
                    except Exception as e:
                        logger.warning(f"Failed to mask name pattern {match}: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Failed to apply name pattern matching: {e}")
            
            return masked_text
        except Exception as e:
            logger.error(f"Failed to mask personal names: {e}", exc_info=True)
            # エラー時は元のテキストを返す（フォールバック）
            return text or ""
    
    def mask_sensitive_info(self, text: str) -> str:
        """
        センシティブ情報をマスキング（エラーハンドリング付き）
        
        Args:
            text: マスキング対象のテキスト
            
        Returns:
            マスキング後のテキスト（エラー時は元のテキストを返す）
        """
        try:
            if not text or not isinstance(text, str):
                return text or ""
            
            masked_text = text
            
            # 金額のマスキング
            try:
                masked_text = re.sub(r'(\d+)億円', r'[金額: \1億円規模]', masked_text)
                masked_text = re.sub(r'(\d+)万円', r'[金額: \1万円規模]', masked_text)
            except Exception as e:
                logger.warning(f"Failed to mask amount: {e}")
            
            # 会社名のマスキング
            try:
                masked_text = re.sub(r'([A-Z])社', r'[顧客名]', masked_text)
            except Exception as e:
                logger.warning(f"Failed to mask company name: {e}")
            
            # プロジェクト名のマスキング
            try:
                masked_text = re.sub(r'プロジェクト([A-Z])', r'[プロジェクト名]', masked_text)
            except Exception as e:
                logger.warning(f"Failed to mask project name: {e}")
            
            return masked_text
        except Exception as e:
            logger.error(f"Failed to mask sensitive info: {e}", exc_info=True)
            # エラー時は元のテキストを返す（フォールバック）
            return text or ""
    
    def mask_meeting_data(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        会議データをマスキング（エラーハンドリング付き）
        
        Args:
            meeting_data: 会議データ
            
        Returns:
            マスキング後の会議データ（エラー時は元のデータを返す）
        """
        try:
            if not meeting_data or not isinstance(meeting_data, dict):
                logger.warning("Invalid meeting_data, returning as-is")
                return meeting_data or {}
            
            masked_data = meeting_data.copy()
            
            # 議事録のマスキング
            if "transcript" in masked_data:
                try:
                    masked_data["transcript"] = self.mask_personal_names(
                        masked_data.get("transcript", ""),
                        meeting_data
                    )
                    masked_data["transcript"] = self.mask_sensitive_info(masked_data.get("transcript", ""))
                except Exception as e:
                    logger.warning(f"Failed to mask transcript: {e}")
            
            # 参加者リストのマスキング（個人名を役職名に置換）
            if "participants" in masked_data:
                try:
                    masked_participants = []
                    participants = masked_data.get("participants", [])
                    if isinstance(participants, list):
                        for participant in participants:
                            try:
                                if isinstance(participant, dict):
                                    masked_participant = participant.copy()
                                    if "name" in masked_participant:
                                        masked_participant["name"] = masked_participant.get("role", "参加者")
                                    masked_participants.append(masked_participant)
                                else:
                                    # 文字列の場合は役職名に置換
                                    masked_participants.append(self._infer_role(str(participant)))
                            except Exception as e:
                                logger.warning(f"Failed to mask participant: {e}")
                                masked_participants.append(participant)  # エラー時は元の値を保持
                    masked_data["participants"] = masked_participants
                except Exception as e:
                    logger.warning(f"Failed to mask participants: {e}")
            
            return masked_data
        except Exception as e:
            logger.error(f"Failed to mask meeting data: {e}", exc_info=True)
            # エラー時は元のデータを返す（フォールバック）
            return meeting_data or {}
    
    def mask_chat_data(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        チャットデータをマスキング
        
        Args:
            chat_data: チャットデータ
            
        Returns:
            マスキング後のチャットデータ
        """
        masked_data = chat_data.copy()
        
        # メッセージのマスキング
        if "messages" in masked_data:
            masked_messages = []
            for message in masked_data["messages"]:
                masked_message = message.copy()
                if "text" in masked_message:
                    masked_message["text"] = self.mask_personal_names(masked_message["text"])
                    masked_message["text"] = self.mask_sensitive_info(masked_message["text"])
                if "user" in masked_message:
                    masked_message["user"] = self._infer_role(masked_message["user"])
                masked_messages.append(masked_message)
            masked_data["messages"] = masked_messages
        
        return masked_data
    
    def _infer_role(self, name: str) -> str:
        """
        名前から役職を推測（簡易版）
        
        Args:
            name: 名前
            
        Returns:
            役職名
        """
        # 既存のマッピングを確認
        if name in self.role_mapping:
            return self.role_mapping[name]
        
        # 簡易的な推測（実際の実装では組織グラフを参照）
        if "CEO" in name or "ceo" in name.lower():
            return "CEO"
        elif "CFO" in name or "cfo" in name.lower():
            return "CFO"
        elif "本部長" in name:
            return "本部長"
        elif "部長" in name:
            return "部長"
        elif "マネージャー" in name or "Manager" in name:
            return "マネージャー"
        else:
            return "参加者"
