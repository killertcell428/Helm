"""
Google Meet API統合
議事録の取得とパース
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import re
from utils.logger import logger
from utils.exceptions import ServiceError


class GoogleMeetService:
    """Google Meet議事録サービス"""
    
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
                logger.info(f"Google Meet API: OAuth認証モード（認証情報: {self.oauth_credentials_file}）")
            else:
                logger.info(f"Google Meet API: サービスアカウントモード（認証情報: {self.credentials_path}）")
        else:
            logger.info("Google Meet API: モックモード")
    
    def get_transcript(self, meeting_id: str) -> Dict[str, Any]:
        """
        議事録を取得
        
        Args:
            meeting_id: 会議ID（会議コードまたは会議名）
            
        Returns:
            議事録データ
        """
        if self.use_mock:
            return self._get_mock_transcript(meeting_id)
        
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
                        service_name="GoogleMeetService",
                        details={"credentials_file": self.oauth_credentials_file}
                    )
            else:
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/meetings.space.readonly']
                )
            
            # Google Meet APIサービスを構築
            service = build('meet', 'v2', credentials=credentials)
            
            try:
                # Google Meet API v2を使用して議事録を取得
                # 注意: 議事録の取得には、会議が終了している必要があります
                # また、会議コードから会議レコードを取得する必要があります
                
                transcript_text = ""
                meeting_info = None
                
                # 会議コードから会議情報を取得
                # Google Meet API v2では、会議コード（meeting code）から会議レコードを取得する必要があります
                # まず、会議スペース（space）を取得または作成する必要がある場合があります
                
                try:
                    # 会議コードから会議レコードを取得
                    # Google Meet API v2では、会議コードから直接会議レコードを取得する方法が限定的です
                    # 会議が終了した後に会議レコードが生成されます
                    
                    conference_record_name = None
                    
                    # 会議IDが会議レコードIDの形式（conferenceRecords/{record_id}）の場合
                    if meeting_id.startswith("conferenceRecords/"):
                        conference_record_name = meeting_id
                    else:
                        # 会議コードから会議レコードを検索
                        # 会議レコードをリストして、該当する会議を探す
                        # 注意: この方法は効率的ではないため、実際の実装では会議コードと会議レコードのマッピングが必要です
                        try:
                            # 最近の会議レコードをリスト（最大100件）
                            # 実際の実装では、フィルタリングやページネーションを使用することを推奨
                            conference_records_response = service.conferenceRecords().list(
                                pageSize=100
                            ).execute()
                            
                            conference_records = conference_records_response.get('conferenceRecords', [])
                            
                            # 会議コードに一致する会議レコードを検索
                            # 注意: 会議レコードには会議コードが直接含まれていない可能性があります
                            # 実際の実装では、会議コードと会議レコードのマッピングテーブルが必要です
                            
                            # 暫定的な実装: 最初の会議レコードを使用（実際の実装では適切な検索ロジックが必要）
                            if conference_records:
                                # 会議コードが会議レコード名に含まれているか確認
                                for record in conference_records:
                                    record_name = record.get('name', '')
                                    # 会議コードが会議レコード名に含まれている場合（暫定的な検索）
                                    if meeting_id in record_name or record_name.endswith(meeting_id):
                                        conference_record_name = record_name
                                        break
                                
                                # 一致する会議レコードが見つからない場合、最新の会議レコードを使用
                                if not conference_record_name and conference_records:
                                    logger.warning(f"Google Meet API: 会議コード '{meeting_id}' に一致する会議レコードが見つかりませんでした")
                                    logger.warning(f"Google Meet API: 最新の会議レコードを使用します（暫定的な実装）")
                                    conference_record_name = conference_records[0].get('name')
                            else:
                                logger.warning(f"Google Meet API: 会議レコードが見つかりませんでした")
                                logger.warning(f"Google Meet API: 会議が終了していないか、会議レコードが生成されていない可能性があります")
                                logger.warning(f"Google Meet API: モックモードにフォールバックします")
                                return self._get_mock_transcript(meeting_id)
                                
                        except HttpError as e:
                            # 会議レコードのリスト取得に失敗した場合
                            status = e.resp.status
                            if status in [400, 403, 404]:
                                logger.warning(f"Google Meet API: 会議レコードの取得に失敗しました: {e}")
                                logger.warning(f"Google Meet API: モックモードにフォールバックします")
                                return self._get_mock_transcript(meeting_id)
                            else:
                                raise
                    
                    if not conference_record_name:
                        logger.warning(f"Google Meet API: 会議レコード名を取得できませんでした")
                        logger.warning(f"Google Meet API: モックモードにフォールバックします")
                        return self._get_mock_transcript(meeting_id)
                    
                    # 会議レコードから議事録を取得
                    # 会議レコードには複数の議事録が含まれる可能性があります
                    # 最新の議事録を取得するか、すべての議事録を取得します
                    
                    # 議事録をリスト
                    transcripts_response = service.conferenceRecords().transcripts().list(
                        parent=conference_record_name
                    ).execute()
                    
                    transcripts = transcripts_response.get('transcripts', [])
                    
                    if not transcripts:
                        logger.warning(f"Google Meet API: 会議レコード '{conference_record_name}' に議事録が見つかりませんでした")
                        logger.warning(f"Google Meet API: 会議が終了していないか、議事録が生成されていない可能性があります")
                        logger.warning(f"Google Meet API: モックモードにフォールバックします")
                        return self._get_mock_transcript(meeting_id)
                    
                    # 最新の議事録を取得（最初の議事録を使用）
                    latest_transcript = transcripts[0]
                    transcript_name = latest_transcript.get('name')
                    
                    # 議事録の詳細を取得
                    transcript_detail = service.conferenceRecords().transcripts().get(
                        name=transcript_name
                    ).execute()
                    
                    # 議事録エントリを取得
                    transcript_entries_response = service.conferenceRecords().transcripts().entries().list(
                        parent=transcript_name
                    ).execute()
                    
                    entries = transcript_entries_response.get('transcriptEntries', [])
                    
                    # 議事録テキストを構築
                    transcript_lines = []
                    for entry in entries:
                        # エントリの種類に応じて処理
                        # Google Meet API v2の議事録エントリの構造に基づく
                        if 'userEvents' in entry:
                            # ユーザーイベント（発言など）
                            for event in entry['userEvents']:
                                if 'message' in event:
                                    message = event['message']
                                    display_name = message.get('displayName', 'Unknown')
                                    text_content = message.get('text', '')
                                    if text_content:
                                        transcript_lines.append(f"{display_name}: {text_content}")
                        elif 'content' in entry:
                            # コンテンツエントリ（テキスト）
                            content = entry['content']
                            if isinstance(content, str):
                                transcript_lines.append(content)
                            elif isinstance(content, dict):
                                # 構造化されたコンテンツの場合
                                text = content.get('text', '')
                                if text:
                                    transcript_lines.append(text)
                        elif 'text' in entry:
                            # テキストエントリ（後方互換性）
                            transcript_lines.append(entry['text'])
                    
                    transcript_text = "\n".join(transcript_lines)
                    
                    # 会議情報を取得
                    conference_record = service.conferenceRecords().get(
                        name=conference_record_name
                    ).execute()
                    
                    meeting_info = {
                        "conference_record_name": conference_record_name,
                        "start_time": conference_record.get('startTime'),
                        "end_time": conference_record.get('endTime'),
                    }
                    
                    logger.info(f"Google Meet API: 議事録を取得しました（会議レコード: {conference_record_name}、エントリ数: {len(entries)}）")
                    
                    return {
                        "meeting_id": meeting_id,
                        "transcript": transcript_text,
                        "metadata": {
                            **meeting_info,
                            "transcript_count": len(transcripts),
                            "entry_count": len(entries),
                            "created_at": datetime.now().isoformat()
                        },
                        "created_at": datetime.now().isoformat()
                    }
                    
                except HttpError as e:
                    status = e.resp.status
                    error_details = str(e)
                    
                    # エラーメッセージをユーザーフレンドリーに変換
                    user_friendly_messages = {
                        400: "会議IDの形式が正しくありません。会議IDを確認してください。",
                        403: "この会議へのアクセス権限がありません。会議の主催者または参加者である必要があります。",
                        404: "指定された会議が見つかりません。会議IDが正しいか、会議が終了しているか確認してください。",
                    }
                    
                    if status == 400:
                        # 400エラー: 無効な会議ID
                        user_message = user_friendly_messages.get(status, f"Google Meet APIでエラーが発生しました: {error_details}")
                        logger.warning(f"Google Meet API: {user_message} モックモードにフォールバックします")
                        return self._get_mock_transcript(meeting_id)
                    elif status == 403:
                        # 403エラー: アクセス権限がない
                        user_message = user_friendly_messages.get(status, f"Google Meet APIでエラーが発生しました: {error_details}")
                        logger.warning(f"Google Meet API: {user_message} モックモードにフォールバックします")
                        return self._get_mock_transcript(meeting_id)
                    elif status == 404:
                        # 404エラー: 会議が見つからない
                        user_message = user_friendly_messages.get(status, f"Google Meet APIでエラーが発生しました: {error_details}")
                        logger.warning(f"Google Meet API: {user_message} モックモードにフォールバックします")
                        return self._get_mock_transcript(meeting_id)
                    else:
                        raise ServiceError(
                            message=f"Google Meet APIでエラーが発生しました: {error_details}",
                            service_name="GoogleMeetService",
                            details={"meeting_id": meeting_id, "status": status, "error": str(e)}
                        )
                        
            except HttpError as e:
                # エラーレスポンスの処理
                status = e.resp.status
                error_details = str(e)
                
                if status in [400, 403, 404]:
                    logger.warning(f"Google Meet API: エラーが発生しました。モックモードにフォールバックします: {error_details}")
                    return self._get_mock_transcript(meeting_id)
                else:
                    raise
            
        except ImportError as e:
            logger.warning(f"Google Meet APIライブラリがインストールされていません。モックモードにフォールバックします: {e}")
            return self._get_mock_transcript(meeting_id)
        except HttpError as e:
            # HttpErrorは既に上で処理されているはずですが、念のため
            status = e.resp.status
            if status in [400, 403, 404]:
                logger.warning(f"Google Meet API: エラーが発生しましたが、既にモックモードにフォールバック済みです: {e}")
                return self._get_mock_transcript(meeting_id)
            else:
                logger.error(f"Google Meet APIエラー: {e}", exc_info=True)
                raise ServiceError(
                    message=f"Google Meet APIで議事録取得に失敗しました: {str(e)}",
                    service_name="GoogleMeetService",
                    details={"meeting_id": meeting_id, "error": str(e)}
                )
        except Exception as e:
            logger.error(f"Google Meet API予期しないエラー: {e}", exc_info=True)
            # エラーが発生した場合もモックデータを返す（フォールバック）
            logger.warning(f"Google Meet API: エラーが発生したため、モックモードにフォールバックします: {e}")
            return self._get_mock_transcript(meeting_id)
    
    def _get_mock_transcript(self, meeting_id: str) -> Dict[str, Any]:
        """モック議事録データ（実データベースに基づく）"""
        return {
            "meeting_id": meeting_id,
            "transcript": """
            CFO: モバイルARPUは前年同期比▲6.2%です。
            CFO: 5G設備投資は当初計画比＋18%となっています。
            CFO: DX事業は売上成長しているが利益率は依然▲12%です。
            
            CEO: 厳しいが、我々の戦略自体は間違っていないと思う。
            CEO: 短期的な数値に一喜一憂すべきではない。
            CEO: 各本部はコスト最適化を検討してほしい。
            CEO: 2025年度計画は維持する方向で進めましょう。
            
            通信本部長: ARPU低下は市場要因も大きい。短期では打てる手が限られる。
            
            DX本部長: 今は仕込みのフェーズ。ここで引くと将来がなくなる。
            
            結論:
            - 2025年度計画は維持
            - 各本部はコスト最適化を検討
            - 次回進捗報告は3か月後
            """,
            "metadata": {
                "meeting_name": "四半期経営会議",
                "date": "2025-01-15",
                "participants": ["CFO", "CEO", "通信本部長", "DX本部長"],
                "duration_minutes": 60
            },
            "created_at": datetime.now().isoformat()
        }
    
    def parse_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        議事録をパースして構造化
        
        Args:
            transcript: 議事録テキスト
            
        Returns:
            構造化された議事録データ
        """
        # 発言者と発言内容を抽出
        speaker_pattern = r'^([^:]+):\s*(.+)$'
        lines = transcript.strip().split('\n')
        
        statements = []
        current_speaker = None
        current_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            match = re.match(speaker_pattern, line)
            if match:
                # 前の発言を保存
                if current_speaker and current_text:
                    statements.append({
                        "speaker": current_speaker,
                        "text": " ".join(current_text)
                    })
                
                # 新しい発言者
                current_speaker = match.group(1).strip()
                current_text = [match.group(2).strip()]
            else:
                # 発言の続き
                if current_text:
                    current_text.append(line)
        
        # 最後の発言を保存
        if current_speaker and current_text:
            statements.append({
                "speaker": current_speaker,
                "text": " ".join(current_text)
            })
        
        # KPI関連キーワードの検出
        kpi_keywords = ["KPI", "目標", "達成", "未達", "下方修正", "成長率", "ARPU", "利益率"]
        kpi_mentions = []
        for stmt in statements:
            for keyword in kpi_keywords:
                if keyword in stmt["text"]:
                    kpi_mentions.append({
                        "speaker": stmt["speaker"],
                        "text": stmt["text"],
                        "keyword": keyword
                    })
                    break
        
        # 撤退/ピボット議論の検出
        exit_keywords = ["撤退", "中止", "ピボット", "方向転換", "やめる"]
        exit_mentioned = any(
            any(keyword in stmt["text"] for keyword in exit_keywords)
            for stmt in statements
        )
        
        return {
            "statements": statements,
            "kpi_mentions": kpi_mentions,
            "exit_discussed": exit_mentioned,
            "total_statements": len(statements)
        }

