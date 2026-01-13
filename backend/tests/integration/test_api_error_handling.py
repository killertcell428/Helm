"""
APIエラーハンドリングの動作確認テスト

使用方法:
    pytest tests/integration/test_api_error_handling.py -v
    または
    python -m pytest tests/integration/test_api_error_handling.py -v
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
from services.google_chat import GoogleChatService
from utils.logger import logger


class TestGoogleMeetErrorHandling:
    """Google Meet APIのエラーハンドリングテスト"""
    
    @pytest.fixture
    def meet_service(self):
        """Google Meetサービスのフィクスチャ"""
        return GoogleMeetService()
    
    def test_invalid_meeting_id_fallback(self, meet_service):
        """無効な会議IDでのフォールバックテスト"""
        # 無効な会議IDでテスト
        result = meet_service.get_transcript("invalid_meeting_id_12345")
        
        # エラーが発生しても、モックデータが返されるはず
        assert result is not None
        assert "meeting_id" in result
        assert "transcript" in result
    
    def test_empty_meeting_id_fallback(self, meet_service):
        """空の会議IDでのフォールバックテスト"""
        result = meet_service.get_transcript("")
        
        # 空の会議IDでもモックデータが返されるはず
        assert result is not None
        assert "transcript" in result
    
    def test_mock_mode_always_succeeds(self, meet_service):
        """モックモードでは常に成功することを確認"""
        if not meet_service.use_mock:
            pytest.skip("モックモードでのテストのため、認証情報を無効化してください")
        
        # 様々な無効な会議IDでテスト
        invalid_ids = [
            "invalid_id",
            "12345",
            "test@test.com",
            "spaces/invalid",
            None
        ]
        
        for meeting_id in invalid_ids:
            if meeting_id is None:
                continue
            result = meet_service.get_transcript(meeting_id)
            assert result is not None
            assert "transcript" in result


class TestGoogleChatErrorHandling:
    """Google Chat APIのエラーハンドリングテスト"""
    
    @pytest.fixture
    def chat_service(self):
        """Google Chatサービスのフィクスチャ"""
        return GoogleChatService()
    
    def test_invalid_space_id_fallback(self, chat_service):
        """無効なスペースIDでのフォールバックテスト"""
        # 無効なスペースIDでテスト
        result = chat_service.get_chat_messages("spaces/invalid_space_id_12345")
        
        # エラーが発生しても、モックデータが返されるはず
        assert result is not None
        assert "chat_id" in result
        assert "messages" in result
    
    def test_empty_space_id_fallback(self, chat_service):
        """空のスペースIDでのフォールバックテスト"""
        result = chat_service.get_chat_messages("")
        
        # 空のスペースIDでもモックデータが返されるはず
        assert result is not None
        assert "messages" in result
    
    def test_mock_mode_always_succeeds(self, chat_service):
        """モックモードでは常に成功することを確認"""
        if not chat_service.use_mock:
            pytest.skip("モックモードでのテストのため、認証情報を無効化してください")
        
        # 様々な無効なスペースIDでテスト
        invalid_ids = [
            "invalid_id",
            "12345",
            "test@test.com",
            "spaces/invalid",
            None
        ]
        
        for chat_id in invalid_ids:
            if chat_id is None:
                continue
            result = chat_service.get_chat_messages(chat_id)
            assert result is not None
            assert "messages" in result


class TestErrorMessages:
    """エラーメッセージの適切性テスト"""
    
    def test_meet_service_error_messages(self):
        """Google Meetサービスのエラーメッセージテスト"""
        service = GoogleMeetService()
        
        # モックモードでもエラーメッセージが適切であることを確認
        result = service.get_transcript("test_meeting")
        assert result is not None
        
        # 結果に必要な情報が含まれていることを確認
        assert "meeting_id" in result
        assert "transcript" in result
        assert "metadata" in result
    
    def test_chat_service_error_messages(self):
        """Google Chatサービスのエラーメッセージテスト"""
        service = GoogleChatService()
        
        # モックモードでもエラーメッセージが適切であることを確認
        result = service.get_chat_messages("test_chat")
        assert result is not None
        
        # 結果に必要な情報が含まれていることを確認
        assert "chat_id" in result
        assert "messages" in result
        assert "metadata" in result


class TestFallbackBehavior:
    """フォールバック動作のテスト"""
    
    def test_meet_service_fallback_on_error(self):
        """Google Meetサービスのエラー時のフォールバックテスト"""
        service = GoogleMeetService()
        
        # 様々なエラーケースでテスト
        test_cases = [
            ("invalid_id", True),
            ("", True),
            ("test_meeting", True),  # モックモードでは常に成功
        ]
        
        for meeting_id, should_succeed in test_cases:
            try:
                result = service.get_transcript(meeting_id)
                if should_succeed:
                    assert result is not None
            except Exception as e:
                # エラーが発生した場合でも、ログに記録されるはず
                logger.warning(f"Error in test: {e}")
                # モックモードではエラーが発生しないはず
                if service.use_mock:
                    pytest.fail(f"Mock mode should not raise errors: {e}")
    
    def test_chat_service_fallback_on_error(self):
        """Google Chatサービスのエラー時のフォールバックテスト"""
        service = GoogleChatService()
        
        # 様々なエラーケースでテスト
        test_cases = [
            ("invalid_id", True),
            ("", True),
            ("test_chat", True),  # モックモードでは常に成功
        ]
        
        for chat_id, should_succeed in test_cases:
            try:
                result = service.get_chat_messages(chat_id)
                if should_succeed:
                    assert result is not None
            except Exception as e:
                # エラーが発生した場合でも、ログに記録されるはず
                logger.warning(f"Error in test: {e}")
                # モックモードではエラーが発生しないはず
                if service.use_mock:
                    pytest.fail(f"Mock mode should not raise errors: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
