"""
Google Drive API統合
結果の保存とダウンロード
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import io
from utils.logger import logger
from utils.exceptions import ServiceError


class GoogleDriveService:
    """Google Driveサービス"""
    
    def __init__(self, credentials_path: Optional[str] = None, shared_drive_id: Optional[str] = None, folder_id: Optional[str] = None):
        """
        Args:
            credentials_path: Google認証情報のパス（Noneの場合はモックデータを使用）
            shared_drive_id: 共有ドライブID（サービスアカウント使用時は必須）
            folder_id: Google DriveフォルダID（OAuth認証使用時、個人フォルダに保存する場合）
        """
        self.credentials_path = credentials_path
        # 環境変数から認証情報を取得（credentials_pathがNoneの場合）
        if self.credentials_path is None:
            self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # 共有ドライブIDを取得（環境変数から）
        self.shared_drive_id = shared_drive_id or os.getenv("GOOGLE_DRIVE_SHARED_DRIVE_ID")
        
        # フォルダIDを取得（環境変数から、OAuth認証で個人フォルダを使用する場合）
        self.folder_id = folder_id or os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        
        # OAuth認証情報を取得
        self.oauth_credentials_file = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE")
        self.oauth_client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        self.oauth_client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        
        # 認証モードの判定
        self.use_oauth = self.oauth_credentials_file is not None and os.path.exists(self.oauth_credentials_file)
        self.use_service_account = self.credentials_path is not None and os.path.exists(self.credentials_path)
        
        # 認証情報ファイルが存在し、有効な場合は実APIを使用
        self.use_mock = not self.use_oauth and not self.use_service_account
        
        if not self.use_mock:
            if self.use_oauth:
                logger.info(f"Google Drive API: OAuth認証モード（認証情報: {self.oauth_credentials_file}）")
                if self.folder_id:
                    logger.info(f"Google Drive API: フォルダID: {self.folder_id}")
                else:
                    logger.warning("Google Drive API: フォルダIDが設定されていません。個人フォルダに保存する場合はフォルダIDが必要です。")
            else:
                logger.info(f"Google Drive API: サービスアカウントモード（認証情報: {self.credentials_path}）")
                if self.shared_drive_id:
                    logger.info(f"Google Drive API: 共有ドライブID: {self.shared_drive_id}")
                else:
                    logger.warning("Google Drive API: 共有ドライブIDが設定されていません。サービスアカウント使用時は共有ドライブが必要です。")
        else:
            logger.info("Google Drive API: モックモード")
    
    def save_file(self, file_name: str, content: bytes, mime_type: str = "application/pdf") -> Dict[str, Any]:
        """
        ファイルを保存
        
        Args:
            file_name: ファイル名
            content: ファイル内容（バイト）
            mime_type: MIMEタイプ
            
        Returns:
            保存されたファイルの情報
        """
        if self.use_mock:
            return self._mock_save_file(file_name, content, mime_type)
        
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseUpload
            from googleapiclient.errors import HttpError
            
            # 認証情報を取得
            if self.use_oauth:
                # OAuth認証を使用
                from .google_drive_oauth import get_oauth_credentials
                credentials = get_oauth_credentials(self.oauth_credentials_file)
                if not credentials:
                    raise ServiceError(
                        message="OAuth認証に失敗しました。認証情報ファイルを確認してください。",
                        service_name="GoogleDriveService",
                        details={"credentials_file": self.oauth_credentials_file}
                    )
            else:
                # サービスアカウント認証を使用
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
            
            # Drive APIサービスを構築
            service = build('drive', 'v3', credentials=credentials)
            
            # ファイルメタデータ
            file_metadata = {
                'name': file_name
            }
            
            # 保存先を設定
            if self.use_oauth and self.folder_id:
                # OAuth認証: 個人フォルダに保存
                file_metadata['parents'] = [self.folder_id]
            elif self.shared_drive_id:
                # サービスアカウント: 共有ドライブに保存
                file_metadata['parents'] = [self.shared_drive_id]
            
            # メディアアップロード
            media = MediaIoBaseUpload(
                io.BytesIO(content),
                mimetype=mime_type,
                resumable=True
            )
            
            # ファイルをアップロード
            create_params = {
                'body': file_metadata,
                'media_body': media,
                'fields': 'id, name, webViewLink, createdTime'
            }
            # 共有ドライブを使用する場合、supportsAllDrives=Trueを設定
            if self.shared_drive_id:
                create_params['supportsAllDrives'] = True
                create_params['supportsTeamDrives'] = True  # 後方互換性のため
            
            file = service.files().create(**create_params).execute()
            
            file_id = file.get('id')
            download_url = f"https://drive.google.com/file/d/{file_id}/view"
            
            logger.info(f"Google Drive API: ファイルを保存しました - {file_name} (ID: {file_id})")
            
            return {
                "file_id": file_id,
                "file_name": file.get('name', file_name),
                "mime_type": mime_type,
                "download_url": download_url,
                "web_view_link": file.get('webViewLink', download_url),
                "created_at": file.get('createdTime', datetime.now().isoformat())
            }
            
        except ImportError as e:
            logger.warning(f"Google Drive APIライブラリがインストールされていません。モックモードにフォールバックします: {e}")
            return self._mock_save_file(file_name, content, mime_type)
        except HttpError as e:
            error_details = str(e)
            # ストレージクォータエラーの場合、より詳細なメッセージを提供
            if "storageQuotaExceeded" in error_details or "storage quota" in error_details.lower():
                logger.error(f"Google Drive APIエラー: サービスアカウントにはストレージクォータがありません。")
                raise ServiceError(
                    message="サービスアカウントにはストレージクォータがありません。以下のいずれかの方法で解決できます：\n1. 共有ドライブ（Shared Drive）を設定（Google Workspace必要）\n2. OAuth認証で個人のGoogle Driveフォルダを使用（個人アカウント可）\n詳細は SETUP_SHARED_DRIVE.md または SETUP_PERSONAL_DRIVE.md を参照してください。",
                    service_name="GoogleDriveService",
                    details={
                        "file_name": file_name,
                        "error": str(e),
                        "solutions": [
                            "共有ドライブIDを環境変数 GOOGLE_DRIVE_SHARED_DRIVE_ID に設定（Google Workspace必要）",
                            "OAuth認証を使用して個人フォルダに保存（SETUP_PERSONAL_DRIVE.md を参照）"
                        ]
                    }
                )
            logger.error(f"Google Drive APIエラー: {e}", exc_info=True)
            raise ServiceError(
                message=f"Google Drive APIでファイル保存に失敗しました: {str(e)}",
                service_name="GoogleDriveService",
                details={"file_name": file_name, "error": str(e)}
            )
        except Exception as e:
            logger.error(f"Google Drive API予期しないエラー: {e}", exc_info=True)
            raise ServiceError(
                message=f"ファイル保存中にエラーが発生しました: {str(e)}",
                service_name="GoogleDriveService",
                details={"file_name": file_name}
            )
    
    def _mock_save_file(self, file_name: str, content: bytes, mime_type: str) -> Dict[str, Any]:
        """モックファイル保存"""
        return {
            "file_id": f"file_{datetime.now().timestamp()}",
            "file_name": file_name,
            "mime_type": mime_type,
            "download_url": f"https://drive.google.com/file/d/mock_file_id/view",
            "web_view_link": f"https://drive.google.com/file/d/mock_file_id/view",
            "created_at": datetime.now().isoformat()
        }
    
    def get_file_download_url(self, file_id: str) -> str:
        """
        ファイルのダウンロードURLを取得
        
        Args:
            file_id: ファイルID
            
        Returns:
            ダウンロードURL
        """
        if self.use_mock:
            return f"https://drive.google.com/file/d/{file_id}/view"
        
        try:
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
            
            # 認証情報を取得
            if self.use_oauth:
                from .google_drive_oauth import get_oauth_credentials
                credentials = get_oauth_credentials(self.oauth_credentials_file)
                if not credentials:
                    # 認証失敗時は標準URLを返す
                    return f"https://drive.google.com/file/d/{file_id}/view"
            else:
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
            
            # Drive APIサービスを構築
            service = build('drive', 'v3', credentials=credentials)
            
            # ファイル情報を取得
            get_params = {
                'fileId': file_id,
                'fields': 'id, name, webViewLink'
            }
            # 共有ドライブを使用する場合、supportsAllDrives=Trueを設定
            if self.shared_drive_id:
                get_params['supportsAllDrives'] = True
                get_params['supportsTeamDrives'] = True  # 後方互換性のため
            
            file = service.files().get(**get_params).execute()
            
            web_view_link = file.get('webViewLink')
            if web_view_link:
                return web_view_link
            
            # webViewLinkが取得できない場合は、標準URLを返す
            return f"https://drive.google.com/file/d/{file_id}/view"
            
        except ImportError:
            logger.warning("Google Drive APIライブラリがインストールされていません。モックモードにフォールバックします。")
            return f"https://drive.google.com/file/d/{file_id}/view"
        except HttpError as e:
            logger.error(f"Google Drive APIエラー: {e}", exc_info=True)
            # エラーが発生しても、標準URLを返す（モックと同様の動作）
            return f"https://drive.google.com/file/d/{file_id}/view"
        except Exception as e:
            logger.error(f"Google Drive API予期しないエラー: {e}", exc_info=True)
            return f"https://drive.google.com/file/d/{file_id}/view"
    
    def share_file(self, file_id: str, emails: List[str], role: str = "reader") -> Dict[str, Any]:
        """
        ファイルを共有
        
        Args:
            file_id: ファイルID
            emails: 共有先メールアドレスリスト
            role: 権限（reader, writer, commenter）
            
        Returns:
            共有結果
        """
        if self.use_mock:
            return self._mock_share_file(file_id, emails, role)
        
        try:
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
            
            # 権限のマッピング
            role_mapping = {
                "reader": "reader",
                "writer": "writer",
                "commenter": "commenter"
            }
            drive_role = role_mapping.get(role, "reader")
            
            # 認証情報を取得
            if self.use_oauth:
                from .google_drive_oauth import get_oauth_credentials
                credentials = get_oauth_credentials(self.oauth_credentials_file)
                if not credentials:
                    raise ServiceError(
                        message="OAuth認証に失敗しました。認証情報ファイルを確認してください。",
                        service_name="GoogleDriveService",
                        details={"credentials_file": self.oauth_credentials_file}
                    )
            else:
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
            
            # Drive APIサービスを構築
            service = build('drive', 'v3', credentials=credentials)
            
            # 各メールアドレスに共有権限を付与
            shared_with = []
            for email in emails:
                try:
                    permission = {
                        'type': 'user',
                        'role': drive_role,
                        'emailAddress': email
                    }
                    create_params = {
                        'fileId': file_id,
                        'body': permission,
                        'fields': 'id'
                    }
                    # 共有ドライブを使用する場合、supportsAllDrives=Trueを設定
                    if self.shared_drive_id:
                        create_params['supportsAllDrives'] = True
                        create_params['supportsTeamDrives'] = True  # 後方互換性のため
                    
                    service.permissions().create(**create_params).execute()
                    shared_with.append(email)
                    logger.info(f"Google Drive API: ファイル {file_id} を {email} と共有しました（権限: {drive_role}）")
                except HttpError as e:
                    logger.warning(f"Google Drive API: {email} への共有に失敗しました: {e}")
                    # 個別のエラーは無視して続行
            
            return {
                "file_id": file_id,
                "shared_with": shared_with,
                "role": role,
                "shared_at": datetime.now().isoformat()
            }
            
        except ImportError:
            logger.warning("Google Drive APIライブラリがインストールされていません。モックモードにフォールバックします。")
            return self._mock_share_file(file_id, emails, role)
        except HttpError as e:
            logger.error(f"Google Drive APIエラー: {e}", exc_info=True)
            raise ServiceError(
                message=f"Google Drive APIでファイル共有に失敗しました: {str(e)}",
                service_name="GoogleDriveService",
                details={"file_id": file_id, "emails": emails, "error": str(e)}
            )
        except Exception as e:
            logger.error(f"Google Drive API予期しないエラー: {e}", exc_info=True)
            raise ServiceError(
                message=f"ファイル共有中にエラーが発生しました: {str(e)}",
                service_name="GoogleDriveService",
                details={"file_id": file_id, "emails": emails}
            )
    
    def _mock_share_file(self, file_id: str, emails: List[str], role: str) -> Dict[str, Any]:
        """モックファイル共有"""
        return {
            "file_id": file_id,
            "shared_with": emails,
            "role": role,
            "shared_at": datetime.now().isoformat()
        }

