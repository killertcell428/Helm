"""
Google Meet API実装の動作確認テスト

使用方法:
    # 環境変数が設定されていることを確認
    # .envファイルまたは環境変数に以下が設定されている必要があります:
    # GOOGLE_OAUTH_CREDENTIALS_FILE=path/to/oauth_credentials.json
    # GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json（サービスアカウント使用時）
    # GOOGLE_CLOUD_PROJECT_ID=your-project-id
    
    pytest tests/integration/test_google_meet_real.py -v
    または
    python -m pytest tests/integration/test_google_meet_real.py -v
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

from services.google_meet import GoogleMeetService
from utils.logger import logger


@pytest.fixture
def meet_service():
    """Google Meetサービスのフィクスチャ"""
    return GoogleMeetService()


def test_meet_service_initialization(meet_service):
    """Google Meetサービスの初期化テスト"""
    assert meet_service is not None
    
    # 認証情報の確認
    oauth_credentials_file = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if oauth_credentials_file and os.path.exists(oauth_credentials_file):
        assert not meet_service.use_mock, "OAuth認証情報がある場合、モックモードではないはず"
        assert meet_service.use_oauth, "OAuth認証モードであるはず"
    elif credentials_path and os.path.exists(credentials_path):
        assert not meet_service.use_mock, "サービスアカウント認証情報がある場合、モックモードではないはず"
        assert meet_service.use_service_account, "サービスアカウント認証モードであるはず"
    else:
        assert meet_service.use_mock, "認証情報がない場合、モックモードであるはず"


def test_get_transcript_mock_mode(meet_service):
    """モックモードでの議事録取得テスト"""
    if not meet_service.use_mock:
        pytest.skip("モックモードでのテストのため、認証情報を無効化してください")
    
    result = meet_service.get_transcript("test_meeting_id")
    
    assert result is not None
    assert "meeting_id" in result
    assert "transcript" in result
    assert "metadata" in result
    assert result["meeting_id"] == "test_meeting_id"
    assert len(result["transcript"]) > 0


def test_get_transcript_real_api(meet_service):
    """実APIモードでの議事録取得テスト（オプション）"""
    if meet_service.use_mock:
        pytest.skip("実APIモードでのテストのため、認証情報を設定してください")
    
    # 実際の会議IDが必要な場合、環境変数から取得
    test_meeting_id = os.getenv("TEST_MEETING_ID")
    
    if not test_meeting_id:
        pytest.skip("実APIテストには TEST_MEETING_ID 環境変数が必要です")
    
    result = meet_service.get_transcript(test_meeting_id)
    
    assert result is not None
    assert "meeting_id" in result
    assert "transcript" in result
    assert "metadata" in result


def test_parse_transcript(meet_service):
    """議事録パースのテスト"""
    # テスト用の議事録テキスト
    test_transcript = """
    CFO: モバイルARPUは前年同期比▲6.2%です。
    CFO: 5G設備投資は当初計画比＋18%となっています。
    CEO: 厳しいが、我々の戦略自体は間違っていないと思う。
    通信本部長: ARPU低下は市場要因も大きい。
    """
    
    parsed = meet_service.parse_transcript(test_transcript)
    
    assert parsed is not None
    assert "statements" in parsed
    assert "kpi_mentions" in parsed
    assert "exit_discussed" in parsed
    assert "total_statements" in parsed
    assert parsed["total_statements"] > 0
    assert len(parsed["statements"]) > 0


def test_error_handling_invalid_meeting_id(meet_service):
    """無効な会議IDでのエラーハンドリングテスト"""
    # 無効な会議IDでテスト
    # モックモードでは常に成功するため、実APIモードでのみテスト
    if meet_service.use_mock:
        pytest.skip("エラーハンドリングテストは実APIモードで実行してください")
    
    # 実APIモードでは、無効な会議IDでもモックにフォールバックするはず
    result = meet_service.get_transcript("invalid_meeting_id_12345")
    
    # エラーが発生しても、モックデータが返されるはず
    assert result is not None
    assert "meeting_id" in result


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
        service = GoogleMeetService()
        
        # モックモードで動作するはず
        assert service.use_mock, "認証情報がない場合、モックモードであるはず"
        
        # モックモードでも議事録を取得できるはず
        result = service.get_transcript("test_meeting")
        assert result is not None
        
    finally:
        # 認証情報を復元
        if original_oauth:
            os.environ["GOOGLE_OAUTH_CREDENTIALS_FILE"] = original_oauth
        if original_sa:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = original_sa


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
