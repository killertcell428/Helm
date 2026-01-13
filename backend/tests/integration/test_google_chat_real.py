"""
Google Chat API実装の動作確認テスト

使用方法:
    # 環境変数が設定されていることを確認
    # .envファイルまたは環境変数に以下が設定されている必要があります:
    # GOOGLE_OAUTH_CREDENTIALS_FILE=path/to/oauth_credentials.json
    # GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json（サービスアカウント使用時）
    # GOOGLE_CLOUD_PROJECT_ID=your-project-id
    
    pytest tests/integration/test_google_chat_real.py -v
    または
    python -m pytest tests/integration/test_google_chat_real.py -v
"""

import os
import sys
import pytest
from pathlib import Path

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

from services.google_chat import GoogleChatService
from utils.logger import logger


@pytest.fixture
def chat_service():
    """Google Chatサービスのフィクスチャ"""
    return GoogleChatService()


def test_chat_service_initialization(chat_service):
    """Google Chatサービスの初期化テスト"""
    assert chat_service is not None
    
    # 認証情報の確認
    oauth_credentials_file = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if oauth_credentials_file and os.path.exists(oauth_credentials_file):
        assert not chat_service.use_mock, "OAuth認証情報がある場合、モックモードではないはず"
        assert chat_service.use_oauth, "OAuth認証モードであるはず"
    elif credentials_path and os.path.exists(credentials_path):
        assert not chat_service.use_mock, "サービスアカウント認証情報がある場合、モックモードではないはず"
        assert chat_service.use_service_account, "サービスアカウント認証モードであるはず"
    else:
        assert chat_service.use_mock, "認証情報がない場合、モックモードであるはず"


def test_get_chat_messages_mock_mode(chat_service):
    """モックモードでのチャットメッセージ取得テスト"""
    if not chat_service.use_mock:
        pytest.skip("モックモードでのテストのため、認証情報を無効化してください")
    
    result = chat_service.get_chat_messages("test_chat_id", "テストチャンネル")
    
    assert result is not None
    assert "chat_id" in result
    assert "messages" in result
    assert "metadata" in result
    assert result["chat_id"] == "test_chat_id"
    assert len(result["messages"]) > 0


def test_get_chat_messages_real_api(chat_service):
    """実APIモードでのチャットメッセージ取得テスト（オプション）"""
    if chat_service.use_mock:
        pytest.skip("実APIモードでのテストのため、認証情報を設定してください")
    
    # 実際のスペースIDが必要な場合、環境変数から取得
    test_chat_id = os.getenv("TEST_CHAT_SPACE_ID")
    
    if not test_chat_id:
        pytest.skip("実APIテストには TEST_CHAT_SPACE_ID 環境変数が必要です")
    
    result = chat_service.get_chat_messages(test_chat_id)
    
    assert result is not None
    assert "chat_id" in result
    assert "messages" in result
    assert "metadata" in result


def test_get_chat_messages_space_id_formats(chat_service):
    """スペースIDの形式テスト"""
    # 形式1: spaces/{space_id}
    result1 = chat_service.get_chat_messages("spaces/test_space_id")
    assert result1 is not None
    
    # 形式2: {space_id}
    result2 = chat_service.get_chat_messages("test_space_id")
    assert result2 is not None


def test_parse_messages(chat_service):
    """メッセージパースのテスト"""
    # テスト用のメッセージリスト（リスクキーワードと反対意見キーワードを含む）
    test_messages = [
        {
            "user": "経営企画A",
            "text": "数字かなり問題がありますね…",
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
    ]
    
    parsed = chat_service.parse_messages(test_messages)
    
    assert parsed is not None
    assert "total_messages" in parsed
    assert "risk_messages" in parsed
    assert "opposition_messages" in parsed
    assert "has_concern" in parsed
    assert parsed["total_messages"] == len(test_messages)
    # "問題"がリスクキーワードに含まれるため、リスクメッセージが検出されるはず
    assert len(parsed["risk_messages"]) > 0
    # "撤退"が反対意見キーワードに含まれるため、反対意見メッセージが検出されるはず
    assert len(parsed["opposition_messages"]) > 0


def test_error_handling_invalid_space_id(chat_service):
    """無効なスペースIDでのエラーハンドリングテスト"""
    # 無効なスペースIDでテスト
    # モックモードでは常に成功するため、実APIモードでのみテスト
    if chat_service.use_mock:
        pytest.skip("エラーハンドリングテストは実APIモードで実行してください")
    
    # 実APIモードでは、無効なスペースIDでもモックにフォールバックするはず
    result = chat_service.get_chat_messages("spaces/invalid_space_id_12345")
    
    # エラーが発生しても、モックデータが返されるはず
    assert result is not None
    assert "chat_id" in result


def test_error_handling_missing_credentials():
    """認証情報がない場合のエラーハンドリングテスト"""
    # 一時的に認証情報を無効化
    original_oauth = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_FILE")
    original_sa = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    
    try:
        if "GOOGLE_OAUTH_CREDENTIALS_FILE" in os.environ:
            del os.environ["GOOGLE_OAUTH_CREDENTIALS_FILE"]
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        
        # 認証情報なしでサービスを初期化
        service = GoogleChatService()
        
        # モックモードで動作するはず
        assert service.use_mock, "認証情報がない場合、モックモードであるはず"
        
        # モックモードでもメッセージを取得できるはず
        result = service.get_chat_messages("test_chat")
        assert result is not None
        
    finally:
        # 認証情報を復元
        if original_oauth:
            os.environ["GOOGLE_OAUTH_CREDENTIALS_FILE"] = original_oauth
        if original_sa:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = original_sa


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
