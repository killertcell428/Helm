"""
LLM統合機能のテスト
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.llm_service import LLMService
from services.prompts import AnalysisPromptBuilder, TaskGenerationPromptBuilder
from services.evaluation import EvaluationParser
from services.output_service import OutputService
import json
import tempfile
import os
from pathlib import Path


class TestAnalysisPromptBuilder:
    """分析用プロンプトビルダーのテスト"""
    
    def test_build_with_meeting_data(self):
        """会議データのみでプロンプトを構築"""
        meeting_data = {
            "transcript": "会議の議事録テキスト",
            "statements": [
                {"speaker": "User1", "text": "発言1"},
                {"speaker": "User2", "text": "発言2"}
            ]
        }
        
        prompt = AnalysisPromptBuilder.build(meeting_data)
        
        assert "会議議事録" in prompt
        assert "会議の議事録テキスト" in prompt or "User1: 発言1" in prompt
        assert "JSON形式" in prompt
    
    def test_build_with_all_data(self):
        """会議・チャット・会議資料すべてでプロンプトを構築"""
        meeting_data = {"transcript": "会議テキスト"}
        chat_data = {"messages": [{"author": "User1", "text": "チャット1"}]}
        materials_data = {"content": "会議資料の内容"}
        
        prompt = AnalysisPromptBuilder.build(meeting_data, chat_data, materials_data)
        
        assert "会議議事録" in prompt
        assert "チャットログ" in prompt
        assert "会議資料" in prompt
    
    def test_get_response_schema(self):
        """レスポンススキーマの取得"""
        schema = AnalysisPromptBuilder.get_response_schema()
        
        assert schema["type"] == "object"
        assert "findings" in schema["properties"]
        assert "overall_score" in schema["properties"]


class TestTaskGenerationPromptBuilder:
    """タスク生成用プロンプトビルダーのテスト"""
    
    def test_build_with_analysis_result(self):
        """分析結果と承認データでプロンプトを構築"""
        analysis_result = {
            "findings": [
                {
                    "pattern_id": "B1_正当化フェーズ",
                    "description": "問題の説明",
                    "severity": "HIGH",
                    "score": 75
                }
            ]
        }
        approval_data = {
            "decision": "approve",
            "modifications": None
        }
        
        prompt = TaskGenerationPromptBuilder.build(analysis_result, approval_data)
        
        assert "分析結果" in prompt
        assert "Executive承認内容" in prompt
        assert "B1_正当化フェーズ" in prompt
        assert "JSON形式" in prompt
    
    def test_get_response_schema(self):
        """レスポンススキーマの取得"""
        schema = TaskGenerationPromptBuilder.get_response_schema()
        
        assert schema["type"] == "object"
        assert "tasks" in schema["properties"]
        assert "execution_plan" in schema["properties"]


class TestEvaluationParser:
    """評価パーサーのテスト"""
    
    def test_parse_analysis_response_valid_json(self):
        """有効なJSONレスポンスのパース"""
        response_text = json.dumps({
            "findings": [
                {
                    "pattern_id": "B1_正当化フェーズ",
                    "severity": "HIGH",
                    "score": 75,
                    "description": "問題の説明",
                    "evidence": ["証拠1", "証拠2"]
                }
            ],
            "overall_score": 75,
            "severity": "HIGH",
            "urgency": "HIGH",
            "explanation": "説明文"
        })
        
        result = EvaluationParser.parse_analysis_response(response_text)
        
        assert result is not None
        assert result["overall_score"] == 75
        assert len(result["findings"]) == 1
    
    def test_parse_analysis_response_markdown_code_block(self):
        """マークダウンコードブロック内のJSONのパース"""
        response_text = """```json
{
  "findings": [],
  "overall_score": 50,
  "severity": "MEDIUM",
  "urgency": "MEDIUM",
  "explanation": "説明"
}
```"""
        
        result = EvaluationParser.parse_analysis_response(response_text)
        
        assert result is not None
        assert result["overall_score"] == 50
    
    def test_parse_analysis_response_invalid_json(self):
        """無効なJSONレスポンスのパース"""
        response_text = "This is not JSON"
        
        result = EvaluationParser.parse_analysis_response(response_text)
        
        assert result is None
    
    def test_parse_task_generation_response_valid_json(self):
        """有効なタスク生成JSONレスポンスのパース"""
        response_text = json.dumps({
            "tasks": [
                {
                    "id": "task1",
                    "name": "タスク1",
                    "type": "research",
                    "description": "説明"
                }
            ],
            "execution_plan": {
                "total_tasks": 1,
                "estimated_total_duration": "1時間"
            }
        })
        
        result = EvaluationParser.parse_task_generation_response(response_text)
        
        assert result is not None
        assert len(result["tasks"]) == 1
        assert result["execution_plan"]["total_tasks"] == 1


class TestLLMService:
    """LLMサービスのテスト"""
    
    @patch.dict(os.environ, {"USE_LLM": "false"})
    def test_init_without_llm(self):
        """LLM無効時の初期化"""
        service = LLMService()
        
        assert service.use_llm == False
        assert service._vertex_ai_available == False
    
    def test_mock_analyze(self):
        """モック分析の実行"""
        service = LLMService()
        service._vertex_ai_available = False
        
        meeting_data = {
            "kpi_mentions": [{"text": "KPI1"}, {"text": "KPI2"}],
            "exit_discussed": False,
            "statements": [
                {"speaker": "User1", "text": "発言1"},
                {"speaker": "User1", "text": "発言2"},
                {"speaker": "User2", "text": "発言3"}
            ]
        }
        
        result = service._mock_analyze(meeting_data, None, None)
        
        assert "findings" in result
        assert "overall_score" in result
        assert "severity" in result
        assert "urgency" in result
        assert "explanation" in result
    
    def test_mock_generate_tasks(self):
        """モックタスク生成の実行"""
        service = LLMService()
        
        analysis_result = {
            "findings": [{"pattern_id": "B1_正当化フェーズ"}]
        }
        approval_data = {"decision": "approve"}
        
        result = service._mock_generate_tasks(analysis_result, approval_data)
        
        assert "tasks" in result
        assert "execution_plan" in result
        assert len(result["tasks"]) > 0


class TestOutputService:
    """出力サービスのテスト"""
    
    def test_save_analysis_result(self):
        """分析結果の保存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = OutputService(output_dir=tmpdir)
            
            analysis_id = "test_analysis_123"
            analysis_result = {
                "findings": [],
                "overall_score": 50,
                "severity": "MEDIUM",
                "urgency": "MEDIUM",
                "explanation": "説明"
            }
            
            file_info = service.save_analysis_result(analysis_id, analysis_result)
            
            assert file_info["file_id"] == f"analysis_{analysis_id}.json"
            assert file_info["type"] == "analysis"
            
            # ファイルが存在することを確認
            file_path = Path(tmpdir) / file_info["filename"]
            assert file_path.exists()
            
            # ファイル内容を確認
            with open(file_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                assert saved_data["analysis_id"] == analysis_id
                assert saved_data["result"]["overall_score"] == 50
    
    def test_save_task_generation_result(self):
        """タスク生成結果の保存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = OutputService(output_dir=tmpdir)
            
            execution_id = "test_execution_123"
            task_result = {
                "tasks": [{"id": "task1", "name": "タスク1"}],
                "execution_plan": {"total_tasks": 1}
            }
            
            file_info = service.save_task_generation_result(execution_id, task_result)
            
            assert file_info["file_id"] == f"tasks_{execution_id}.json"
            assert file_info["type"] == "tasks"
            
            # ファイルが存在することを確認
            file_path = Path(tmpdir) / file_info["filename"]
            assert file_path.exists()
    
    def test_get_file(self):
        """ファイルの取得"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = OutputService(output_dir=tmpdir)
            
            # テストファイルを作成
            test_data = {"test": "data"}
            file_path = Path(tmpdir) / "test_file.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(test_data, f)
            
            # ファイルを取得
            result = service.get_file("test_file.json")
            
            assert result is not None
            assert result["test"] == "data"
    
    def test_list_files(self):
        """ファイル一覧の取得"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = OutputService(output_dir=tmpdir)
            
            # テストファイルを作成
            for i in range(3):
                file_path = Path(tmpdir) / f"analysis_test_{i}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({"test": i}, f)
            
            # ファイル一覧を取得
            files = service.list_files()
            
            assert len(files) == 3
            assert all(f["type"] == "analysis" for f in files)
            
            # タイプでフィルタ
            files_filtered = service.list_files(file_type="analysis")
            assert len(files_filtered) == 3
