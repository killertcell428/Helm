# Google API統合ガイド

## 概要

このガイドでは、モック実装から実際のGoogle API統合への移行方法を説明します。

## 前提条件

1. Google Cloud Projectが作成されている
2. 必要なAPIが有効化されている
3. サービスアカウントが作成されている
4. 認証情報（JSON）がダウンロードされている

## 必要なAPI

以下のAPIを有効化する必要があります：

- Google Meet API
- Google Chat API
- Google Drive API
- Google Docs API
- Google Sheets API
- Google Slides API
- Vertex AI API

## 認証設定

### 方法1: 環境変数（推奨）

```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
export GOOGLE_CLOUD_PROJECT_ID="your-project-id"
```

### 方法2: コード内で指定

```python
# main.py
meet_service = GoogleMeetService(credentials_path="path/to/credentials.json")
```

## 実装が必要な箇所

### 1. Google Meet API

**ファイル**: `services/google_meet.py`

```python
def get_transcript(self, meeting_id: str) -> Dict[str, Any]:
    if self.use_mock:
        return self._get_mock_transcript(meeting_id)
    
    # 実装が必要
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    
    credentials = service_account.Credentials.from_service_account_file(
        self.credentials_path,
        scopes=['https://www.googleapis.com/auth/meetings.space.readonly']
    )
    
    service = build('meet', 'v2', credentials=credentials)
    # API呼び出しを実装
```

### 2. Google Chat API

**ファイル**: `services/google_chat.py`

```python
def get_chat_messages(self, chat_id: str, channel_name: Optional[str] = None) -> Dict[str, Any]:
    if self.use_mock:
        return self._get_mock_messages(chat_id, channel_name)
    
    # 実装が必要
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    
    credentials = service_account.Credentials.from_service_account_file(
        self.credentials_path,
        scopes=['https://www.googleapis.com/auth/chat.messages.readonly']
    )
    
    service = build('chat', 'v1', credentials=credentials)
    # API呼び出しを実装
```

### 3. Google Drive API

**ファイル**: `services/google_drive.py`

```python
def save_file(self, file_name: str, content: bytes, mime_type: str = "application/pdf") -> Dict[str, Any]:
    if self.use_mock:
        return self._mock_save_file(file_name, content, mime_type)
    
    # 実装が必要
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    import io
    
    credentials = service_account.Credentials.from_service_account_file(
        self.credentials_path,
        scopes=['https://www.googleapis.com/auth/drive.file']
    )
    
    service = build('drive', 'v3', credentials=credentials)
    
    file_metadata = {'name': file_name}
    media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=True)
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()
    
    return {
        "file_id": file.get('id'),
        "file_name": file.get('name'),
        "download_url": f"https://drive.google.com/file/d/{file.get('id')}/view",
        "web_view_link": file.get('webViewLink'),
        "created_at": datetime.now().isoformat()
    }
```

### 4. Google Workspace API

**ファイル**: `services/google_workspace.py`

#### Google Docs API

```python
def generate_document(self, content: Dict[str, Any], document_type: str = "document") -> Dict[str, Any]:
    if self.use_mock:
        return self._mock_document(content, document_type)
    
    # 実装が必要
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    
    credentials = service_account.Credentials.from_service_account_file(
        self.credentials_path,
        scopes=['https://www.googleapis.com/auth/documents']
    )
    
    service = build('docs', 'v1', credentials=credentials)
    # ドキュメント作成を実装
```

#### Google Sheets API

```python
# 同様にGoogle Sheets APIを実装
```

#### Google Slides API

```python
# 同様にGoogle Slides APIを実装
```

## 実装の優先順位

1. **Google Drive API** - ファイル保存・ダウンロード（最重要）
2. **Google Docs API** - 資料作成
3. **Google Chat API** - チャット取得
4. **Google Meet API** - 議事録取得

## 注意事項

1. **API制限**: 各APIにはレート制限があります
2. **コスト**: API使用にはコストが発生する場合があります
3. **権限**: サービスアカウントに適切な権限を付与する必要があります
4. **エラーハンドリング**: 実APIではエラーハンドリングが重要です

## テスト方法

実API統合後は、以下を確認：

1. 実際にGoogle Driveにファイルが作成される
2. 実際にGoogle Docsで資料が作成される
3. 実際にGoogle Chatからメッセージが取得される
4. 実際にGoogle Meetから議事録が取得される

## トラブルシューティング

### 認証エラー

```bash
# 認証情報のパスを確認
echo $GOOGLE_APPLICATION_CREDENTIALS

# 認証情報ファイルの存在を確認
ls -la path/to/credentials.json
```

### API有効化エラー

Google Cloud Consoleで、必要なAPIが有効化されているか確認

### 権限エラー

サービスアカウントに適切な権限（IAMロール）が付与されているか確認

