"""
LLM統合サービス
Vertex AI / Gemini API / Gen AI SDK の統合レイヤー
"""

import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from utils.logger import logger
from config import config
from services.prompts import AnalysisPromptBuilder, TaskGenerationPromptBuilder
from services.evaluation import EvaluationParser

# Gen AI SDK（google-generativeai）がインストールされている場合は優先的に利用
try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


class LLMService:
    """LLM統合サービス"""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        """
        Args:
            project_id: Google Cloud Project ID
            location: Vertex AIのリージョン（デフォルト: us-central1、環境変数 VERTEX_AI_LOCATION で変更可能）
            model_name: 使用するモデル名（デフォルト: gemini-1.5-flash-002）
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT_ID") or config.GOOGLE_CLOUD_PROJECT_ID
        self.location = location or os.getenv("VERTEX_AI_LOCATION", "us-central1")
        # Gen AI SDK用のモデル名（models/プレフィックス付き、利用可能な最新安定版）
        # デフォルト: models/gemini-2.0-flash-001 (Stable version)
        self.model_name = model_name or os.getenv("LLM_MODEL", "models/gemini-2.0-flash-001")
        self.use_llm = os.getenv("USE_LLM", "false").lower() == "true"
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        self.timeout = int(os.getenv("LLM_TIMEOUT", "60"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.top_p = float(os.getenv("LLM_TOP_P", "0.95"))
        
        # Gen AI SDK用の設定（GOOGLE_API_KEY があれば優先利用）
        self.genai_api_key = os.getenv("GOOGLE_API_KEY")
        self._genai_available = _GENAI_AVAILABLE and bool(self.genai_api_key)
        if self._genai_available:
            try:
                genai.configure(api_key=self.genai_api_key)
                logger.info("Gen AI SDK configured with GOOGLE_API_KEY")
            except Exception as e:
                logger.warning(f"Gen AI SDKの初期化に失敗しました: {e}。Vertex AI経由にフォールバックします。")
                self._genai_available = False
        
        # Vertex AIの利用可能性をチェック
        self._check_vertex_ai_availability()
    
    def _check_vertex_ai_availability(self):
        """Vertex AIが利用可能かチェック"""
        if not self.use_llm or not self.project_id:
            self._vertex_ai_available = False
            logger.info("LLM統合が無効化されています（USE_LLM=false または GOOGLE_CLOUD_PROJECT_ID未設定）")
            return
        
        try:
            from google.cloud import aiplatform
            self._vertex_ai_available = True
            logger.info(f"Vertex AI利用可能: project={self.project_id}, model={self.model_name}")
        except ImportError:
            logger.warning("google-cloud-aiplatformがインストールされていません。モックモードを使用します。")
            self._vertex_ai_available = False
        except Exception as e:
            logger.warning(f"Vertex AI初期化エラー: {e}。モックモードを使用します。")
            self._vertex_ai_available = False
    
    def analyze_structure(
        self,
        meeting_data: Dict[str, Any],
        chat_data: Optional[Dict[str, Any]] = None,
        materials_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        構造的問題を分析
        
        Args:
            meeting_data: 会議データ（パース済みまたは生データ）
            chat_data: チャットデータ（パース済みまたは生データ、オプション）
            materials_data: 会議資料データ（オプション）
            
        Returns:
            分析結果
        """
        if not self._vertex_ai_available:
            logger.warning("⚠️ LLM統合が無効のため、モック分析結果を返します（USE_LLM=false または GOOGLE_CLOUD_PROJECT_ID未設定）")
            result = self._mock_analyze(meeting_data, chat_data, materials_data)
            result["_is_mock"] = True  # モックデータであることを明示
            result["_llm_status"] = "disabled"
            return result
        
        # プロンプトを構築
        prompt = AnalysisPromptBuilder.build(meeting_data, chat_data, materials_data)
        
        # LLM APIを呼び出し
        response_text = self._call_llm(
            prompt=prompt,
            response_format="json",
            model_name=self.model_name
        )
        
        if not response_text:
            logger.warning(
                "LLM API呼び出し失敗、モック分析結果にフォールバック",
                extra={
                    "meeting_id": meeting_data.get("meeting_id"),
                    "has_chat_data": chat_data is not None,
                    "has_materials_data": materials_data is not None
                }
            )
            return self._mock_analyze(meeting_data, chat_data, materials_data)
        
        # レスポンスをパース
        parsed_result = EvaluationParser.parse_analysis_response(response_text)
        
        if not parsed_result:
            logger.warning(
                "LLMレスポンスのパース失敗、モック分析結果にフォールバック",
                extra={
                    "response_length": len(response_text) if response_text else 0,
                    "response_preview": response_text[:200] if response_text else None
                }
            )
            return self._mock_analyze(meeting_data, chat_data, materials_data)
        
        # タイムスタンプを追加
        parsed_result["created_at"] = datetime.now().isoformat()
        parsed_result["_is_mock"] = False  # LLM生成データであることを明示
        parsed_result["_llm_status"] = "success"
        parsed_result["_llm_model"] = self.model_name
        
        logger.info(f"✅ LLM分析完了（実際のLLM生成）: overall_score={parsed_result.get('overall_score', 0)}, model={self.model_name}")
        
        return parsed_result
    
    def generate_tasks(
        self,
        analysis_result: Dict[str, Any],
        approval_data: Dict[str, Any],
        approved_interventions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        タスクを生成
        
        Args:
            analysis_result: 分析結果
            approval_data: Executive承認データ
            approved_interventions: 承認された介入案（オプション）
            
        Returns:
            タスク生成結果
        """
        if not self._vertex_ai_available:
            logger.warning("⚠️ LLM統合が無効のため、モックタスク生成結果を返します（USE_LLM=false または GOOGLE_CLOUD_PROJECT_ID未設定）")
            result = self._mock_generate_tasks(analysis_result, approval_data)
            result["_is_mock"] = True  # モックデータであることを明示
            result["_llm_status"] = "disabled"
            return result
        
        # プロンプトを構築
        prompt = TaskGenerationPromptBuilder.build(
            analysis_result,
            approval_data,
            approved_interventions
        )
        
        # LLM APIを呼び出し
        response_text = self._call_llm(
            prompt=prompt,
            response_format="json",
            model_name=self.model_name
        )
        
        if not response_text:
            logger.warning(
                "LLM API呼び出し失敗、モックタスク生成結果にフォールバック",
                extra={
                    "analysis_id": analysis_result.get("analysis_id"),
                    "approval_decision": approval_data.get("decision")
                }
            )
            return self._mock_generate_tasks(analysis_result, approval_data)
        
        # レスポンスをパース
        parsed_result = EvaluationParser.parse_task_generation_response(response_text)
        
        if not parsed_result:
            logger.warning(
                "LLMレスポンスのパース失敗、モックタスク生成結果にフォールバック",
                extra={
                    "response_length": len(response_text) if response_text else 0,
                    "response_preview": response_text[:200] if response_text else None
                }
            )
            return self._mock_generate_tasks(analysis_result, approval_data)
        
        parsed_result["_is_mock"] = False  # LLM生成データであることを明示
        parsed_result["_llm_status"] = "success"
        parsed_result["_llm_model"] = self.model_name
        
        logger.info(f"✅ LLMタスク生成完了（実際のLLM生成）: total_tasks={parsed_result.get('execution_plan', {}).get('total_tasks', 0)}, model={self.model_name}")
        
        return parsed_result
    
    def _call_llm(
        self,
        prompt: str,
        response_format: str = "text",
        model_name: Optional[str] = None
    ) -> Optional[str]:
        """
        LLM APIを呼び出し（Gen AI SDK専用）
        
        Args:
            prompt: プロンプト
            response_format: レスポンス形式（"text" または "json"）
            model_name: モデル名（オプション）
            
        Returns:
            レスポンステキスト、失敗時はNone
        """
        model = model_name or self.model_name
        
        # Gen AI SDK（google-generativeai）のみを使用
        if not self._genai_available:
            logger.warning("Gen AI SDKが利用できません（GOOGLE_API_KEY未設定またはgoogle-generativeai未インストール）")
            return None
        
        # モデル名をGen AI SDK用に調整（models/プレフィックスを追加）
        genai_model_name = model
        if not genai_model_name.startswith("models/"):
            # プレフィックスがない場合は追加
            genai_model_name = f"models/{genai_model_name}"
            logger.info(f"モデル名を調整: {model} → {genai_model_name}")
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                # Gen AI SDKでモデルを初期化
                gen_model = genai.GenerativeModel(genai_model_name)
                
                # 生成設定
                generation_config = {
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "max_output_tokens": 8192,
                }
                
                # JSON形式を強制する場合
                if response_format == "json":
                    generation_config["response_mime_type"] = "application/json"
                
                # LLM API呼び出し
                resp = gen_model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                elapsed_time = time.time() - start_time
                
                if not resp:
                    logger.warning(f"Gen AI SDKからの空レスポンス（試行 {attempt + 1}/{self.max_retries}）")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)  # 指数バックオフ
                        continue
                    return None
                
                # レスポンステキストを取得
                response_text = getattr(resp, "text", None)
                if not response_text:
                    logger.warning(f"Gen AI SDKからのレスポンスにtext属性がありません（試行 {attempt + 1}/{self.max_retries}）")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return None
                
                logger.info(f"Gen AI SDK呼び出し成功: model={genai_model_name}, elapsed={elapsed_time:.2f}s")
                return response_text
                
            except Exception as e:
                error_type = type(e).__name__
                logger.error(
                    f"Gen AI SDK呼び出しエラー（試行 {attempt + 1}/{self.max_retries}）: {e}",
                    extra={
                        "error_type": error_type,
                        "model": genai_model_name,
                        "attempt": attempt + 1,
                        "max_retries": self.max_retries,
                        "project_id": self.project_id
                    },
                    exc_info=True
                )
                if attempt < self.max_retries - 1:
                    # 指数バックオフでリトライ
                    delay = config.RETRY_INITIAL_DELAY * (config.RETRY_BACKOFF_BASE ** attempt)
                    logger.info(f"Retrying after {delay:.2f} seconds...")
                    time.sleep(delay)
                    continue
                logger.error(f"Gen AI SDK呼び出しが{self.max_retries}回失敗しました。")
                return None
        
        return None
    
    def _mock_analyze(
        self,
        meeting_data: Dict[str, Any],
        chat_data: Optional[Dict[str, Any]] = None,
        materials_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """モック分析結果（フォールバック用）"""
        findings = []
        
        # 会議データから情報を取得
        kpi_mentions = meeting_data.get("kpi_mentions", [])
        exit_discussed = meeting_data.get("exit_discussed", False)
        statements = meeting_data.get("statements", [])
        
        # 判断集中率の計算
        if statements:
            from collections import Counter
            speakers = [stmt.get("speaker", "Unknown") for stmt in statements]
            speaker_counts = Counter(speakers)
            max_speaker_count = max(speaker_counts.values())
            decision_concentration_rate = max_speaker_count / len(statements)
        else:
            decision_concentration_rate = 0.0
        
        # 反対意見の無視
        ignored_opposition_count = 0
        if chat_data:
            opposition_messages = chat_data.get("opposition_messages", [])
            if opposition_messages and not exit_discussed:
                ignored_opposition_count = len(opposition_messages)
        
        # 正当化フェーズの検出
        if len(kpi_mentions) >= 2 and not exit_discussed and decision_concentration_rate >= 0.4:
            findings.append({
                "pattern_id": "B1_正当化フェーズ",
                "severity": "HIGH",
                "score": 75,
                "description": "KPI悪化認識があるが戦略変更議論がない",
                "evidence": [
                    f"KPI下方修正が{len(kpi_mentions)}回検出",
                    "撤退/ピボット議論が一度も行われていない",
                    f"判断集中率: {decision_concentration_rate:.2%}",
                    f"反対意見無視: {ignored_opposition_count}件"
                ],
                "quantitative_scores": {
                    "kpi_downgrade_count": len(kpi_mentions),
                    "exit_discussed": exit_discussed,
                    "decision_concentration_rate": decision_concentration_rate,
                    "ignored_opposition_count": ignored_opposition_count
                }
            })
        
        overall_score = max([f.get("score", 0) for f in findings], default=0)
        severity = "HIGH" if overall_score >= 70 else "MEDIUM" if overall_score >= 40 else "LOW"
        urgency = "HIGH" if overall_score >= 70 else "MEDIUM" if overall_score >= 40 else "LOW"
        
        explanation = "構造的問題は検出されませんでした。"
        if findings:
            finding = findings[0]
            explanation = (
                f"【重要度: {finding.get('severity', 'MEDIUM')} / 緊急度: {urgency}】 "
                f"{finding.get('description', '')} "
                f"証拠: {', '.join(finding.get('evidence', [])[:2])}"
            )
        
        return {
            "findings": findings,
            "overall_score": overall_score,
            "severity": severity,
            "urgency": urgency,
            "explanation": explanation,
            "created_at": datetime.now().isoformat(),
            "_is_mock": True,  # モックデータであることを明示
            "_llm_status": "mock_fallback"
        }
    
    def _mock_generate_tasks(
        self,
        analysis_result: Dict[str, Any],
        approval_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """モックタスク生成結果（フォールバック用）"""
        tasks = [
            {
                "id": "task1",
                "name": "市場データ分析",
                "type": "research",
                "description": "競合他社のARPU推移、業界平均との比較データを収集・分析",
                "dependencies": [],
                "estimated_duration": "2時間",
                "expected_output": "市場データ分析レポート"
            },
            {
                "id": "task2",
                "name": "社内データ統合",
                "type": "analysis",
                "description": "過去の戦略変更事例、類似プロジェクトの成功/失敗データを抽出",
                "dependencies": [],
                "estimated_duration": "1時間",
                "expected_output": "社内データ統合レポート"
            },
            {
                "id": "task3",
                "name": "3案比較資料の自動生成",
                "type": "document",
                "description": "継続案、縮小案、撤退案の財務シミュレーションを含む3案比較資料を生成",
                "dependencies": ["task1", "task2"],
                "estimated_duration": "3時間",
                "expected_output": "3案比較資料（Google Docs）"
            },
            {
                "id": "task4",
                "name": "関係部署への事前通知",
                "type": "notification",
                "description": "CFO、各本部長に議題と背景資料を自動配信",
                "dependencies": ["task3"],
                "estimated_duration": "30分",
                "expected_output": "通知送信完了（8名）"
            },
            {
                "id": "task5",
                "name": "会議アジェンダの更新",
                "type": "calendar",
                "description": "次回経営会議のカレンダーと資料を自動更新",
                "dependencies": ["task3"],
                "estimated_duration": "30分",
                "expected_output": "会議アジェンダ更新完了"
            }
        ]
        
        return {
            "tasks": tasks,
            "execution_plan": {
                "total_tasks": len(tasks),
                "estimated_total_duration": "7時間",
                "critical_path": ["task1", "task2", "task3", "task4", "task5"]
            },
            "_is_mock": True,  # モックデータであることを明示
            "_llm_status": "mock_fallback"
        }
