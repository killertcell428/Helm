"""
Google Workspace API統合
リサーチ・分析・資料作成
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import json
from utils.logger import logger
from utils.exceptions import ServiceError


class GoogleWorkspaceService:
    """Google Workspaceサービス"""
    
    def __init__(self, credentials_path: Optional[str] = None, folder_id: Optional[str] = None):
        """
        Args:
            credentials_path: Google認証情報のパス（サービスアカウント使用時、Noneの場合はモックデータを使用）
            folder_id: Google DriveフォルダID（OAuth認証使用時、個人フォルダに保存する場合）
        """
        self.credentials_path = credentials_path
        # 環境変数から認証情報を取得（credentials_pathがNoneの場合）
        if self.credentials_path is None:
            self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # フォルダIDを取得（環境変数から、OAuth認証で個人フォルダを使用する場合）
        self.folder_id = folder_id or os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        
        # OAuth認証情報を取得
        self.oauth_credentials_file = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE")
        
        # 認証モードの判定
        self.use_oauth = self.oauth_credentials_file is not None and os.path.exists(self.oauth_credentials_file)
        self.use_service_account = self.credentials_path is not None and os.path.exists(self.credentials_path)
        
        # 認証情報ファイルが存在し、有効な場合は実APIを使用
        self.use_mock = not self.use_oauth and not self.use_service_account
        
        if not self.use_mock:
            if self.use_oauth:
                logger.info(f"Google Workspace API: OAuth認証モード（認証情報: {self.oauth_credentials_file}）")
            else:
                logger.info(f"Google Workspace API: サービスアカウントモード（認証情報: {self.credentials_path}）")
        else:
            logger.info("Google Workspace API: モックモード")
    
    def research_market_data(self, topic: str) -> Dict[str, Any]:
        """
        市場データをリサーチ
        
        Args:
            topic: リサーチトピック
            
        Returns:
            リサーチ結果
        """
        if self.use_mock:
            return self._mock_research(topic)
        
        # TODO: 実際のGoogle Workspace API統合
        # Google Search APIやVertex AI Searchを使用
        
        return self._mock_research(topic)
    
    def _mock_research(self, topic: str) -> Dict[str, Any]:
        """モックリサーチ結果"""
        return {
            "topic": topic,
            "results": [
                {
                    "source": "業界レポート",
                    "title": "通信業界のARPU動向",
                    "summary": "業界平均ARPUは前年同期比▲5.1%",
                    "url": "https://example.com/report1"
                },
                {
                    "source": "競合分析",
                    "title": "主要競合他社のARPU推移",
                    "summary": "A社: ▲3.2%, B社: ▲7.8%, C社: ▲4.5%",
                    "url": "https://example.com/report2"
                }
            ],
            "created_at": datetime.now().isoformat()
        }
    
    def analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        データを分析
        
        Args:
            data: 分析対象データ
            
        Returns:
            分析結果
        """
        if self.use_mock:
            return self._mock_analysis(data)
        
        # TODO: Vertex AI / Geminiでデータ分析
        
        return self._mock_analysis(data)
    
    def _mock_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """モック分析結果"""
        return {
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
            },
            "created_at": datetime.now().isoformat()
        }
    
    def generate_document(self, content: Dict[str, Any], document_type: str = "document") -> Dict[str, Any]:
        """
        資料を生成
        
        Args:
            content: 資料内容
            document_type: 資料タイプ（document, presentation, spreadsheet）
            
        Returns:
            生成された資料の情報
        """
        if self.use_mock:
            return self._mock_document(content, document_type)
        
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
                        service_name="GoogleWorkspaceService",
                        details={"credentials_file": self.oauth_credentials_file}
                    )
            else:
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/documents']
                )
            
            # 資料タイプに応じてAPIを選択
            if document_type == "document":
                # Google Docs APIを使用
                service = build('docs', 'v1', credentials=credentials)
                document = self._create_google_doc(service, content, self.folder_id)
            elif document_type == "presentation":
                # Google Slides APIを使用（将来実装）
                logger.warning("Google Slides APIは未実装です。モックモードにフォールバックします。")
                return self._mock_document(content, document_type)
            elif document_type == "spreadsheet":
                # Google Sheets APIを使用（将来実装）
                logger.warning("Google Sheets APIは未実装です。モックモードにフォールバックします。")
                return self._mock_document(content, document_type)
            else:
                # デフォルトはGoogle Docs
                service = build('docs', 'v1', credentials=credentials)
                document = self._create_google_doc(service, content, self.folder_id)
            
            document_id = document.get('documentId')
            title = content.get('title', '3案比較資料')
            
            # コンテンツを挿入
            if content.get('content'):
                self._insert_content_to_doc(service, document_id, content.get('content'))
            
            # Google Driveフォルダに移動（フォルダIDが指定されている場合）
            if self.folder_id and self.use_oauth:
                # ドキュメントをフォルダに移動（Drive APIを使用）
                try:
                    drive_service = build('drive', 'v3', credentials=credentials)
                    # 既存の親フォルダを取得
                    file = drive_service.files().get(
                        fileId=document_id,
                        fields='parents'
                    ).execute()
                    previous_parents = ",".join(file.get('parents', []))
                    # 新しいフォルダに移動
                    drive_service.files().update(
                        fileId=document_id,
                        addParents=self.folder_id,
                        removeParents=previous_parents,
                        fields='id, parents'
                    ).execute()
                    logger.info(f"Google Docs API: ドキュメントをフォルダに移動しました: {self.folder_id}")
                except Exception as e:
                    logger.warning(f"Google Docs API: フォルダへの移動に失敗しました（ドキュメントは作成済み）: {e}")
            
            download_url = f"https://docs.google.com/document/d/{document_id}/edit"
            
            logger.info(f"Google Docs API: ドキュメントを生成しました - {title} (ID: {document_id})")
            
            return {
                "document_id": document_id,
                "document_type": document_type,
                "title": title,
                "download_url": download_url,
                "view_url": f"https://docs.google.com/document/d/{document_id}/view",
                "edit_url": download_url,
                "created_at": datetime.now().isoformat()
            }
            
        except ImportError as e:
            logger.warning(f"Google Docs APIライブラリがインストールされていません。モックモードにフォールバックします: {e}")
            return self._mock_document(content, document_type)
        except HttpError as e:
            status = e.resp.status if hasattr(e, 'resp') else None
            error_details = str(e)
            
            # エラーメッセージをユーザーフレンドリーに変換
            user_friendly_messages = {
                400: "ドキュメント生成のリクエストが無効です。入力内容を確認してください。",
                401: "認証に失敗しました。認証情報を確認してください。",
                403: "ドキュメント生成の権限がありません。Google Driveへの書き込み権限を確認してください。",
                404: "必要なリソースが見つかりません。フォルダIDが正しいか確認してください。",
                429: "リクエストが多すぎます。しばらく待ってから再度お試しください。",
            }
            
            user_message = user_friendly_messages.get(status, f"Google Docs APIでドキュメント生成に失敗しました: {error_details}")
            logger.error(f"Google Docs APIエラー: {user_message}", exc_info=True)
            raise ServiceError(
                message=user_message,
                service_name="GoogleWorkspaceService",
                details={"document_type": document_type, "status": status, "error": error_details}
            )
        except Exception as e:
            logger.error(f"Google Docs API予期しないエラー: {e}", exc_info=True)
            raise ServiceError(
                message=f"ドキュメント生成中にエラーが発生しました: {str(e)}",
                service_name="GoogleWorkspaceService",
                details={"document_type": document_type}
            )
    
    def _create_google_doc(self, service, content: Dict[str, Any], folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Google Docsドキュメントを作成
        
        Args:
            service: Google Docs APIサービス
            content: ドキュメント内容
            folder_id: 保存先フォルダID（OAuth認証使用時）
            
        Returns:
            作成されたドキュメント情報
        """
        title = content.get('title', '3案比較資料')
        
        # ドキュメントを作成
        document = service.documents().create(
            body={'title': title}
        ).execute()
        
        return document
    
    def _insert_content_to_doc(self, service, document_id: str, content_text: str):
        """
        Google Docsドキュメントにコンテンツを挿入
        
        Args:
            service: Google Docs APIサービス
            document_id: ドキュメントID
            content_text: 挿入するテキスト
        """
        if not content_text:
            return
        
        try:
            # ドキュメントの構造を取得（最初の位置を確認）
            doc = service.documents().get(documentId=document_id).execute()
            # ドキュメントの最後の位置を取得
            end_index = doc.get('body', {}).get('content', [{}])[-1].get('endIndex', 1)
            
            # テキストを挿入（最後の位置に）
            requests = [
                {
                    'insertText': {
                        'location': {
                            'index': end_index - 1  # 最後の位置の前に挿入
                        },
                        'text': content_text
                    }
                }
            ]
            
            service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            logger.info(f"Google Docs API: コンテンツを挿入しました（長さ: {len(content_text)}文字）")
        except Exception as e:
            logger.warning(f"Google Docs API: コンテンツの挿入に失敗しました（ドキュメントは作成済み）: {e}")
    
    def _mock_document(self, content: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """モック資料生成"""
        return {
            "document_id": f"doc_{datetime.now().timestamp()}",
            "document_type": document_type,
            "title": content.get("title", "3案比較資料"),
            "download_url": "https://drive.google.com/file/d/mock_file_id/view",
            "created_at": datetime.now().isoformat()
        }
    
    def send_notification(self, recipients: List[str], message: str, subject: str) -> Dict[str, Any]:
        """
        通知を送信
        
        Args:
            recipients: 受信者リスト
            message: メッセージ
            subject: 件名
            
        Returns:
            送信結果
        """
        if self.use_mock:
            return self._mock_notification(recipients, message, subject)
        
        # TODO: Gmail API / Google Chat APIで通知送信
        
        return self._mock_notification(recipients, message, subject)
    
    def _mock_notification(self, recipients: List[str], message: str, subject: str) -> Dict[str, Any]:
        """モック通知送信"""
        return {
            "sent_to": recipients,
            "subject": subject,
            "message": message,
            "status": "sent",
            "sent_at": datetime.now().isoformat()
        }

