"""
Google Chat API統合
会議後のチャット取得とパース
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import re
from utils.logger import logger
from utils.exceptions import ServiceError


class GoogleChatService:
    """Google Chatサービス"""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Args:
            credentials_path: Google認証情報のパス（サービスアカウント使用時、Noneの場合はモックデータを使用）
        """
        self.credentials_path = credentials_path
        # 環境変数から認証情報を取得（credentials_pathがNoneの場合）
        if self.credentials_path is None:
            self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # OAuth認証情報を取得
        self.oauth_credentials_file = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE")
        
        # 認証モードの判定
        self.use_oauth = self.oauth_credentials_file is not None and os.path.exists(self.oauth_credentials_file)
        self.use_service_account = self.credentials_path is not None and os.path.exists(self.credentials_path)
        
        # 認証情報ファイルが存在し、有効な場合は実APIを使用
        self.use_mock = not self.use_oauth and not self.use_service_account
        
        if not self.use_mock:
            if self.use_oauth:
                logger.info(f"Google Chat API: OAuth認証モード（認証情報: {self.oauth_credentials_file}）")
            else:
                logger.info(f"Google Chat API: サービスアカウントモード（認証情報: {self.credentials_path}）")
        else:
            logger.info("Google Chat API: モックモード")
    
    def get_chat_messages(self, chat_id: str, channel_name: Optional[str] = None) -> Dict[str, Any]:
        """
        チャットメッセージを取得
        
        Args:
            chat_id: チャットID（スペース名またはスペースID）
            channel_name: チャンネル名（オプション）
            
        Returns:
            チャットメッセージデータ
        """
        if self.use_mock:
            return self._get_mock_messages(chat_id, channel_name)
        
        try:
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
            
            # 認証情報を取得
            if self.use_oauth:
                from .google_drive_oauth import get_oauth_credentials
                credentials = get_oauth_credentials(self.oauth_credentials_file)
                if not credentials:
                    raise ServiceError(
                        message="OAuth認証に失敗しました。認証情報ファイルを確認してください。",
                        service_name="GoogleChatService",
                        details={"credentials_file": self.oauth_credentials_file}
                    )
            else:
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/chat.messages.readonly']
                )
            
            # Google Chat APIサービスを構築
            service = build('chat', 'v1', credentials=credentials)
            
            # スペース（チャットルーム）のメッセージを取得
            # 注意: Google Chat APIはスペース名またはスペースIDが必要
            # スペース名の形式: spaces/{space_id} または {space_id}
            try:
                # スペース名の形式を正規化
                if chat_id.startswith("spaces/"):
                    space_name = chat_id
                else:
                    # スペースIDのみが提供されている場合、spaces/プレフィックスを追加
                    space_name = f"spaces/{chat_id}"
                
                # メッセージを取得
                messages_response = service.spaces().messages().list(
                    parent=space_name,
                    pageSize=100  # 最大100件まで取得
                ).execute()
                
                messages = messages_response.get('messages', [])
                
                # メッセージをパースして構造化
                parsed_messages = []
                for msg in messages:
                    # メッセージの構造を解析
                    text = ""
                    user = "Unknown"
                    timestamp = ""
                    
                    # テキストメッセージの場合
                    if 'text' in msg:
                        text = msg['text']
                    
                    # 送信者情報
                    if 'sender' in msg:
                        sender = msg['sender']
                        if 'name' in sender:
                            user = sender['name']
                        elif 'displayName' in sender:
                            user = sender['displayName']
                    
                    # タイムスタンプ
                    if 'createTime' in msg:
                        timestamp = msg['createTime']
                    
                    parsed_messages.append({
                        "user": user,
                        "text": text,
                        "timestamp": timestamp
                    })
                
                logger.info(f"Google Chat API: {len(parsed_messages)}件のメッセージを取得しました（スペース: {space_name}）")
                
                return {
                    "chat_id": chat_id,
                    "channel_name": channel_name or space_name,
                    "messages": parsed_messages,
                    "metadata": {
                        "space_name": space_name,
                        "total_messages": len(parsed_messages)
                    },
                    "created_at": datetime.now().isoformat()
                }
                
            except HttpError as e:
                # エラーレスポンスの処理
                status = e.resp.status
                error_details = str(e)
                
                # エラーメッセージをユーザーフレンドリーに変換
                user_friendly_messages = {
                    400: "チャットスペースIDの形式が正しくありません。スペースIDは 'spaces/{space_id}' の形式で指定してください。",
                    403: "このチャットスペースへのアクセス権限がありません。スペースへのアクセス権限を確認してください。",
                    404: "指定されたチャットスペースが見つかりません。スペースIDが正しいか確認してください。",
                }
                
                if status == 400:
                    # 400エラー: リクエストの形式が間違っている（スペースIDが無効など）
                    user_message = user_friendly_messages.get(status, f"Google Chat APIでエラーが発生しました: {error_details}")
                    logger.warning(f"Google Chat API: {user_message} モックモードにフォールバックします")
                    return self._get_mock_messages(chat_id, channel_name)
                elif status == 403:
                    # 403エラー: アクセス権限がない
                    user_message = user_friendly_messages.get(status, f"Google Chat APIでエラーが発生しました: {error_details}")
                    logger.warning(f"Google Chat API: {user_message} モックモードにフォールバックします")
                    return self._get_mock_messages(chat_id, channel_name)
                elif status == 404:
                    # 404エラー: スペースが見つからない
                    user_message = user_friendly_messages.get(status, f"Google Chat APIでエラーが発生しました: {error_details}")
                    logger.warning(f"Google Chat API: {user_message} モックモードにフォールバックします")
                    return self._get_mock_messages(chat_id, channel_name)
                else:
                    # その他のエラーはServiceErrorとして再スロー
                    raise ServiceError(
                        message=f"Google Chat APIでエラーが発生しました: {error_details}",
                        service_name="GoogleChatService",
                        details={"chat_id": chat_id, "status": status, "error": str(e)}
                    )
            
        except ImportError as e:
            logger.warning(f"Google Chat APIライブラリがインストールされていません。モックモードにフォールバックします: {e}")
            return self._get_mock_messages(chat_id, channel_name)
        except HttpError as e:
            # HttpErrorは既に上で処理されているはずですが、念のため
            status = e.resp.status
            if status in [400, 403, 404]:
                # これらのエラーは既にモックモードにフォールバックされているはず
                logger.warning(f"Google Chat API: エラーが発生しましたが、既にモックモードにフォールバック済みです: {e}")
                return self._get_mock_messages(chat_id, channel_name)
            else:
                logger.error(f"Google Chat APIエラー: {e}", exc_info=True)
                raise ServiceError(
                    message=f"Google Chat APIでメッセージ取得に失敗しました: {str(e)}",
                    service_name="GoogleChatService",
                    details={"chat_id": chat_id, "error": str(e)}
                )
        except Exception as e:
            logger.error(f"Google Chat API予期しないエラー: {e}", exc_info=True)
            # エラーが発生した場合もモックデータを返す（フォールバック）
            logger.warning(f"Google Chat API: エラーが発生したため、モックモードにフォールバックします: {e}")
            return self._get_mock_messages(chat_id, channel_name)
    
    def _get_mock_messages(self, chat_id: str, channel_name: Optional[str]) -> Dict[str, Any]:
        """モックチャットメッセージデータ"""
        return {
            "chat_id": chat_id,
            "channel_name": channel_name or "経営企画チャンネル",
            "messages": [
                {
                    "user": "経営企画A",
                    "text": "数字かなり厳しかったですね…",
                    "timestamp": "2025-01-15T15:30:00Z"
                },
                {
                    "user": "経営企画B",
                    "text": "ですね。ただCEOも今回は触れなかったので、深掘りは次回かなと",
                    "timestamp": "2025-01-15T15:32:00Z"
                },
                {
                    "user": "通信本部補佐",
                    "text": "「撤退」とか言い出す空気ではなかったですね",
                    "timestamp": "2025-01-15T15:35:00Z"
                }
            ],
            "metadata": {
                "project_id": "project_zombie",
                "meeting_id": "meeting_001"
            },
            "created_at": datetime.now().isoformat()
        }
    
    def parse_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        チャットメッセージをパースして構造化
        
        Args:
            messages: メッセージリスト
            
        Returns:
            構造化されたチャットデータ
        """
        # リスク提起メッセージの検出
        risk_keywords = ["やばい", "危険", "リスク", "問題", "止める", "上げた方がいい", "報告"]
        risk_messages = []
        
        for msg in messages:
            text = msg.get("text", "")
            for keyword in risk_keywords:
                if keyword in text:
                    risk_messages.append({
                        "user": msg.get("user"),
                        "text": text,
                        "keyword": keyword,
                        "timestamp": msg.get("timestamp")
                    })
                    break
        
        # エスカレーション完了の検出
        escalation_keywords = ["エスカレーション", "報告", "相談", "上げました", "報告しました"]
        escalation_mentioned = any(
            any(keyword in msg.get("text", "") for keyword in escalation_keywords)
            for msg in messages
        )
        
        # 反対意見の検出
        opposition_keywords = ["やめた方が", "止める", "撤退", "反対", "問題"]
        opposition_messages = []
        
        for msg in messages:
            text = msg.get("text", "")
            for keyword in opposition_keywords:
                if keyword in text:
                    opposition_messages.append({
                        "user": msg.get("user"),
                        "text": text,
                        "keyword": keyword,
                        "timestamp": msg.get("timestamp")
                    })
                    break
        
        return {
            "total_messages": len(messages),
            "risk_messages": risk_messages,
            "escalation_mentioned": escalation_mentioned,
            "opposition_messages": opposition_messages,
            "has_concern": len(risk_messages) > 0 or len(opposition_messages) > 0
        }

