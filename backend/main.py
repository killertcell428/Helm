"""
Helm Backend API - Main Application
Google Meet → 議事録・チャット取得 → 重要性・緊急性評価 → 
人が承認/指示 → Googleサービス経由でリサーチ・分析・資料作成 → 
結果をアプリに返してダウンロード → 次回会議へ
"""

from dotenv import load_dotenv
load_dotenv()  # .envファイルを読み込む

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError as PydanticValidationError
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import traceback
from utils.logger import logger
from utils.exceptions import (
    HelmException,
    ValidationError,
    ServiceError,
    TimeoutError,
    NotFoundError,
    RetryableError
)
from config import config
from services import (
    GoogleMeetService, 
    GoogleChatService, 
    StructureAnalyzer,
    GoogleWorkspaceService,
    GoogleDriveService,
    VertexAIService,
    ScoringService
)
from services.escalation_engine import EscalationEngine

app = FastAPI(
    title=config.API_TITLE,
    description="組織を賢くするAI - Helm Backend API",
    version=config.API_VERSION
)

# CORS設定（フロントエンドとの連携用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== グローバルエラーハンドラー ====================

@app.exception_handler(HelmException)
async def helm_exception_handler(request: Request, exc: HelmException):
    """Helmカスタム例外のハンドラー"""
    error_id = str(uuid.uuid4())
    logger.error(
        f"Error {error_id}: {exc.error_code} - {exc.message}",
        extra={"error_id": error_id, "error_code": exc.error_code, "details": exc.details}
    )
    
    status_code = 400
    if isinstance(exc, NotFoundError):
        status_code = 404
    elif isinstance(exc, TimeoutError):
        status_code = 504
    elif isinstance(exc, ServiceError):
        status_code = 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error_id": error_id,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """バリデーションエラーのハンドラー"""
    error_id = str(uuid.uuid4())
    errors = exc.errors()
    
    logger.warning(
        f"Validation error {error_id}: {errors}",
        extra={"error_id": error_id, "errors": errors}
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error_id": error_id,
            "error_code": "VALIDATION_ERROR",
            "message": "リクエストのバリデーションに失敗しました",
            "details": {"validation_errors": errors}
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP例外のハンドラー"""
    error_id = str(uuid.uuid4())
    logger.warning(
        f"HTTP error {error_id}: {exc.status_code} - {exc.detail}",
        extra={"error_id": error_id, "status_code": exc.status_code}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_id": error_id,
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """すべての未処理例外のハンドラー"""
    error_id = str(uuid.uuid4())
    logger.error(
        f"Unhandled error {error_id}: {str(exc)}",
        exc_info=True,
        extra={"error_id": error_id, "traceback": traceback.format_exc()}
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error_id": error_id,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "内部エラーが発生しました。エラーIDを記録してお問い合わせください。"
        }
    )

# ==================== データモデル ====================

class MeetingIngestRequest(BaseModel):
    meeting_id: str
    transcript: Optional[str] = None
    metadata: Dict[str, Any]

class ChatIngestRequest(BaseModel):
    chat_id: str
    messages: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any]

class AnalyzeRequest(BaseModel):
    meeting_id: str
    chat_id: Optional[str] = None

class EscalateRequest(BaseModel):
    analysis_id: str

class ApproveRequest(BaseModel):
    escalation_id: str
    decision: str  # "approve" or "modify"
    modifications: Optional[Dict[str, Any]] = None

class ExecuteRequest(BaseModel):
    approval_id: str

# ==================== サービス初期化 ====================

meet_service = GoogleMeetService(
    credentials_path=config.GOOGLE_APPLICATION_CREDENTIALS
)  # 環境変数から認証情報を取得（サービスアカウントまたはOAuth）
chat_service = GoogleChatService(
    credentials_path=config.GOOGLE_APPLICATION_CREDENTIALS
)  # 環境変数から認証情報を取得（サービスアカウントまたはOAuth）
vertex_ai_service = VertexAIService()  # モックデータ使用（実際のAPI統合は環境変数設定後）
scoring_service = ScoringService()  # 重要性・緊急性評価サービス
analyzer = StructureAnalyzer(
    use_vertex_ai=False, 
    vertex_ai_service=vertex_ai_service,
    scoring_service=scoring_service
)  # ルールベース分析 + スコアリング
escalation_engine = EscalationEngine(escalation_threshold=config.ESCALATION_THRESHOLD)  # エスカレーション判断エンジン（デモ用に50に設定）
workspace_service = GoogleWorkspaceService(
    credentials_path=config.GOOGLE_APPLICATION_CREDENTIALS,
    folder_id=config.GOOGLE_DRIVE_FOLDER_ID
)  # 環境変数から認証情報を取得（サービスアカウントまたはOAuth）
drive_service = GoogleDriveService(
    credentials_path=config.GOOGLE_APPLICATION_CREDENTIALS,
    shared_drive_id=config.GOOGLE_DRIVE_SHARED_DRIVE_ID,
    folder_id=config.GOOGLE_DRIVE_FOLDER_ID
)  # 環境変数から認証情報を取得（サービスアカウントまたはOAuth）

# ==================== インメモリストレージ（開発用） ====================

meetings_db: Dict[str, Dict] = {}
chats_db: Dict[str, Dict] = {}
analyses_db: Dict[str, Dict] = {}
escalations_db: Dict[str, Dict] = {}
approvals_db: Dict[str, Dict] = {}
executions_db: Dict[str, Dict] = {}

# ==================== APIエンドポイント ====================

@app.get("/")
async def root():
    return {
        "message": "Helm API",
        "version": "0.1.0",
        "status": "running"
    }

@app.post("/api/meetings/ingest")
async def ingest_meeting(request: MeetingIngestRequest):
    """Google Meet議事録の取り込み"""
    try:
        logger.info(f"Meeting ingest request: {request.meeting_id}")
        # 議事録を取得（モックまたは実際のAPI）
        try:
            if not request.transcript:
                # transcriptが空の場合はGoogle Meet APIから取得
                meet_data = meet_service.get_transcript(request.meeting_id)
                transcript = meet_data["transcript"]
                metadata = meet_data.get("metadata", {})
            else:
                transcript = request.transcript
                metadata = request.metadata
        except Exception as e:
            logger.error(f"Failed to get transcript for meeting {request.meeting_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"議事録の取得に失敗しました: {str(e)}",
                service_name="GoogleMeetService",
                details={"meeting_id": request.meeting_id}
            )
        
        # 議事録をパース
        try:
            parsed_data = meet_service.parse_transcript(transcript)
        except Exception as e:
            logger.error(f"Failed to parse transcript for meeting {request.meeting_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"議事録のパースに失敗しました: {str(e)}",
                service_name="GoogleMeetService",
                details={"meeting_id": request.meeting_id}
            )
        
        meeting_data = {
            "meeting_id": request.meeting_id,
            "transcript": transcript,
            "parsed_data": parsed_data,
            "metadata": metadata,
            "ingested_at": datetime.now().isoformat(),
            "status": "ingested"
        }
        meetings_db[request.meeting_id] = meeting_data
        
        logger.info(f"Meeting {request.meeting_id} ingested successfully")
        
        return {
            "meeting_id": request.meeting_id,
            "status": "success",
            "parsed": parsed_data,
            "transcript": transcript,  # 実際の議事録テキストを返す
            "metadata": metadata  # メタデータも返す
        }
    except HelmException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ingest_meeting: {e}", exc_info=True)
        raise

@app.post("/api/chat/ingest")
async def ingest_chat(request: ChatIngestRequest):
    """Google Chatログの取り込み"""
    try:
        logger.info(f"Chat ingest request: {request.chat_id}")
        # チャットメッセージを取得（モックまたは実際のAPI）
        try:
            if not request.messages:
                # messagesが空の場合はGoogle Chat APIから取得
                chat_data_raw = chat_service.get_chat_messages(
                    request.chat_id,
                    request.metadata.get("channel_name")
                )
                messages = chat_data_raw["messages"]
                metadata = chat_data_raw.get("metadata", {})
            else:
                messages = request.messages
                metadata = request.metadata
        except Exception as e:
            logger.error(f"Failed to get chat messages for chat {request.chat_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"チャットメッセージの取得に失敗しました: {str(e)}",
                service_name="GoogleChatService",
                details={"chat_id": request.chat_id}
            )
        
        # チャットメッセージをパース
        try:
            parsed_data = chat_service.parse_messages(messages)
        except Exception as e:
            logger.error(f"Failed to parse chat messages for chat {request.chat_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"チャットメッセージのパースに失敗しました: {str(e)}",
                service_name="GoogleChatService",
                details={"chat_id": request.chat_id}
            )
        
        chat_data = {
            "chat_id": request.chat_id,
            "messages": messages,
            "parsed_data": parsed_data,
            "metadata": metadata,
            "ingested_at": datetime.now().isoformat(),
            "status": "ingested"
        }
        chats_db[request.chat_id] = chat_data
        
        logger.info(f"Chat {request.chat_id} ingested successfully")
        
        return {
            "chat_id": request.chat_id,
            "status": "success",
            "parsed": parsed_data,
            "messages": messages,  # 実際のチャットメッセージを返す
            "metadata": metadata  # メタデータも返す
        }
    except HelmException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ingest_chat: {e}", exc_info=True)
        raise

@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    """構造的問題検知"""
    try:
        logger.info(f"Analysis request: meeting_id={request.meeting_id}, chat_id={request.chat_id}")
        analysis_id = str(uuid.uuid4())
        
        # 会議データとチャットデータを取得
        meeting = meetings_db.get(request.meeting_id)
        if not meeting:
            raise NotFoundError(
                message=f"会議データが見つかりません: {request.meeting_id}",
                resource_type="meeting",
                resource_id=request.meeting_id
            )
        
        chat = chats_db.get(request.chat_id) if request.chat_id else None
        if request.chat_id and not chat:
            logger.warning(f"Chat {request.chat_id} not found, proceeding without chat data")
        
        # 構造的問題検知を実行
        try:
            meeting_parsed = meeting.get("parsed_data", {})
            chat_parsed = chat.get("parsed_data", {}) if chat else None
            
            analysis_result = analyzer.analyze(meeting_parsed, chat_parsed)
        except Exception as e:
            logger.error(f"Failed to analyze: {e}", exc_info=True)
            raise ServiceError(
                message=f"構造的問題検知に失敗しました: {str(e)}",
                service_name="StructureAnalyzer",
                details={"meeting_id": request.meeting_id, "chat_id": request.chat_id}
            )
        
        analysis_data = {
            "analysis_id": analysis_id,
            "meeting_id": request.meeting_id,
            "chat_id": request.chat_id,
            "findings": analysis_result["findings"],
            "scores": analysis_result["scores"],
            "score": analysis_result["overall_score"],
            "severity": analysis_result["severity"],
            "urgency": analysis_result.get("urgency", "MEDIUM"),
            "explanation": analysis_result["explanation"],
            "created_at": analysis_result["created_at"],
            "status": "completed"
        }
        
        analyses_db[analysis_id] = analysis_data
        
        logger.info(f"Analysis {analysis_id} completed: score={analysis_result['overall_score']}, severity={analysis_result['severity']}")
        
        return analysis_data
    except HelmException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze: {e}", exc_info=True)
        raise

@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """分析結果取得"""
    try:
        logger.info(f"Get analysis request: {analysis_id}")
        analysis = analyses_db.get(analysis_id)
        if not analysis:
            raise NotFoundError(
                message=f"分析結果が見つかりません: {analysis_id}",
                resource_type="analysis",
                resource_id=analysis_id
            )
        
        return analysis
    except HelmException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_analysis: {e}", exc_info=True)
        raise

@app.post("/api/escalate")
async def escalate(request: EscalateRequest):
    """Executive呼び出し"""
    try:
        logger.info(f"Escalation request: analysis_id={request.analysis_id}")
        analysis = analyses_db.get(request.analysis_id)
        if not analysis:
            raise NotFoundError(
                message=f"分析結果が見つかりません: {request.analysis_id}",
                resource_type="analysis",
                resource_id=request.analysis_id
            )
        
        # エスカレーション判断エンジンを使用
        try:
            escalation_info = escalation_engine.create_escalation(request.analysis_id, analysis)
        except Exception as e:
            logger.error(f"Failed to create escalation: {e}", exc_info=True)
            raise ServiceError(
                message=f"エスカレーション判断に失敗しました: {str(e)}",
                service_name="EscalationEngine",
                details={"analysis_id": request.analysis_id}
            )
        
        if not escalation_info:
            raise ValidationError(
                message="エスカレーション条件を満たしていません。",
                details={"analysis_id": request.analysis_id, "score": analysis.get("score", 0)}
            )
        
        escalation_id = str(uuid.uuid4())
        
        escalation_data = {
            "escalation_id": escalation_id,
            "analysis_id": request.analysis_id,
            "target_role": escalation_info["target_role"],
            "reason": escalation_info["reason"],
            "severity": escalation_info.get("severity", "MEDIUM"),
            "urgency": escalation_info.get("urgency", "MEDIUM"),
            "score": escalation_info.get("score", 0),
            "created_at": escalation_info["created_at"],
            "status": "pending"
        }
        
        escalations_db[escalation_id] = escalation_data
        
        logger.info(f"Escalation {escalation_id} created: target_role={escalation_info['target_role']}")
        
        return escalation_data
    except HelmException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in escalate: {e}", exc_info=True)
        raise

@app.post("/api/approve")
async def approve(request: ApproveRequest):
    """Executive承認"""
    try:
        logger.info(f"Approval request: escalation_id={request.escalation_id}, decision={request.decision}")
        escalation = escalations_db.get(request.escalation_id)
        if not escalation:
            raise NotFoundError(
                message=f"エスカレーションが見つかりません: {request.escalation_id}",
                resource_type="escalation",
                resource_id=request.escalation_id
            )
        
        # バリデーション
        if request.decision not in ["approve", "modify"]:
            raise ValidationError(
                message=f"無効な決定です: {request.decision}",
                field="decision",
                details={"valid_values": ["approve", "modify"]}
            )
        
        approval_id = str(uuid.uuid4())
        
        approval_data = {
            "approval_id": approval_id,
            "escalation_id": request.escalation_id,
            "decision": request.decision,
            "modifications": request.modifications,
            "created_at": datetime.now().isoformat(),
            "status": "approved"
        }
        
        approvals_db[approval_id] = approval_data
        escalation["status"] = "approved"
        
        logger.info(f"Approval {approval_id} created: decision={request.decision}")
        
        return approval_data
    except HelmException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in approve: {e}", exc_info=True)
        raise

@app.post("/api/execute")
async def execute(request: ExecuteRequest):
    """AI自律実行開始"""
    try:
        logger.info(f"Execution request: approval_id={request.approval_id}")
        approval = approvals_db.get(request.approval_id)
        if not approval:
            raise NotFoundError(
                message=f"承認が見つかりません: {request.approval_id}",
                resource_type="approval",
                resource_id=request.approval_id
            )
        
        execution_id = str(uuid.uuid4())
        
        # タスク定義
        tasks = [
            {"id": "task1", "name": "市場データ分析", "status": "pending", "type": "research"},
            {"id": "task2", "name": "社内データ統合", "status": "pending", "type": "analysis"},
            {"id": "task3", "name": "3案比較資料の自動生成", "status": "pending", "type": "document"},
            {"id": "task4", "name": "関係部署への事前通知", "status": "pending", "type": "notification"},
            {"id": "task5", "name": "会議アジェンダの更新", "status": "pending", "type": "calendar"}
        ]
        
        execution_data = {
            "execution_id": execution_id,
            "approval_id": request.approval_id,
            "status": "running",
            "progress": 0,
            "tasks": tasks,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        executions_db[execution_id] = execution_data
        
        logger.info(f"Execution {execution_id} started: {len(tasks)} tasks")
        
        return execution_data
    except HelmException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in execute: {e}", exc_info=True)
        raise

@app.get("/api/execution/{execution_id}")
async def get_execution(execution_id: str):
    """実行状態取得"""
    try:
        logger.debug(f"Get execution request: {execution_id}")
        execution = executions_db.get(execution_id)
        if not execution:
            raise NotFoundError(
                message=f"実行状態が見つかりません: {execution_id}",
                resource_type="execution",
                resource_id=execution_id
            )
        
        # 進捗を自動的に更新（実際のタスクを実行）
        tasks = execution.get("tasks", [])
        if tasks and execution.get("status") == "running":
            # 経過時間に基づいてタスクを完了状態にする
            created_at_str = execution.get("created_at", datetime.now().isoformat())
            try:
                # ISO形式の文字列をパース（タイムゾーン情報を処理）
                if 'Z' in created_at_str:
                    created_at_str = created_at_str.replace('Z', '+00:00')
                created_at = datetime.fromisoformat(created_at_str)
            except (ValueError, AttributeError):
                # パースに失敗した場合は現在時刻を使用
                created_at = datetime.now()
            
            elapsed_seconds = (datetime.now() - created_at).total_seconds()
            
            # 各タスクを順次完了（2秒ごと）
            completed_count = min(int(elapsed_seconds / 2), len(tasks))
            
            # タスクのステータスを更新（元のリストを変更せずに新しいリストを作成）
            updated_tasks = []
            for i, task in enumerate(tasks):
                task_copy = task.copy() if isinstance(task, dict) else dict(task)
                if i < completed_count and task_copy.get("status") != "completed":
                    # タスクを実行
                    task_copy["status"] = "completed"
                    
                    # 実際のタスクを実行
                    try:
                        if task_copy.get("type") == "document":
                            # 資料生成
                            # 分析データから情報を取得（承認から取得）
                            approval = approvals_db.get(execution.get("approval_id"))
                            escalation = None
                            analysis = None
                            if approval:
                                escalation = escalations_db.get(approval.get("escalation_id"))
                                if escalation:
                                    analysis = analyses_db.get(escalation.get("analysis_id"))
                            
                            # 分析結果から資料内容を生成
                            content_text = "3案比較の詳細分析"
                            if analysis:
                                findings = analysis.get("findings", [])
                                if findings:
                                    content_text = f"構造的問題分析結果\n\n"
                                    for finding in findings:
                                        content_text += f"## {finding.get('pattern_id', '問題')}\n"
                                        content_text += f"{finding.get('description', '')}\n\n"
                            
                            doc_result = workspace_service.generate_document({
                                "title": task_copy.get("name", "3案比較資料"),
                                "content": content_text
                            })
                            
                            # 生成されたドキュメント情報を保存
                            task_copy["result"] = {
                                "document_id": doc_result.get("document_id"),
                                "title": doc_result.get("title"),
                                "download_url": doc_result.get("download_url"),
                                "view_url": doc_result.get("view_url"),
                                "edit_url": doc_result.get("edit_url"),
                                "document_type": doc_result.get("document_type")
                            }
                            logger.info(f"Document generated: {doc_result.get('document_id')} - {doc_result.get('title')}")
                            
                        elif task_copy.get("type") == "research":
                            # リサーチ実行
                            research_result = workspace_service.research_market_data("ARPU動向")
                            task_copy["result"] = {
                                "data": research_result
                            }
                            
                        elif task_copy.get("type") == "analysis":
                            # 分析実行
                            analysis_result = workspace_service.analyze_data({})
                            task_copy["result"] = {
                                "data": analysis_result
                            }
                            
                        elif task_copy.get("type") == "notification":
                            # 通知実行（モック）
                            task_copy["result"] = {
                                "recipients": 8,
                                "status": "sent"
                            }
                            
                    except Exception as e:
                        logger.error(f"Task execution failed: {task_copy.get('name')} - {e}", exc_info=True)
                        task_copy["status"] = "failed"
                        task_copy["error"] = str(e)
                elif i >= completed_count:
                    task_copy["status"] = "pending"
                
                updated_tasks.append(task_copy)
            
            # 進捗を計算
            progress = (completed_count / len(tasks)) * 100 if tasks else 0
            
            # すべてのタスクが完了したらステータスを更新
            if completed_count >= len(tasks):
                execution["status"] = "completed"
                execution["progress"] = 100
            else:
                execution["status"] = "running"
                execution["progress"] = progress
            
            execution["updated_at"] = datetime.now().isoformat()
            execution["tasks"] = updated_tasks
            executions_db[execution_id] = execution  # 更新を保存
        
        return execution
    except HelmException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_execution: {e}", exc_info=True)
        raise

@app.get("/api/execution/{execution_id}/results")
async def get_execution_results(execution_id: str):
    """実行結果取得"""
    try:
        logger.info(f"Get execution results request: {execution_id}")
        execution = executions_db.get(execution_id)
        if not execution:
            raise NotFoundError(
                message=f"実行状態が見つかりません: {execution_id}",
                resource_type="execution",
                resource_id=execution_id
            )
        
        # 実行タスクから結果を生成（保存された結果を使用）
        results_list = []
        
        for task in execution.get("tasks", []):
            if task.get("status") == "completed":
                task_result = task.get("result")
                
                if task.get("type") == "document":
                    # 資料生成結果（保存された結果を使用）
                    if task_result:
                        results_list.append({
                            "type": "document",
                            "name": task.get("name"),
                            "document_id": task_result.get("document_id"),
                            "title": task_result.get("title"),
                            "download_url": task_result.get("download_url"),
                            "view_url": task_result.get("view_url"),
                            "edit_url": task_result.get("edit_url"),
                            "document_type": task_result.get("document_type")
                        })
                    else:
                        # フォールバック: 結果が保存されていない場合は生成
                        logger.warning(f"Document result not found for task {task.get('id')}, generating new document")
                        doc_result = workspace_service.generate_document({
                            "title": task.get("name", "資料"),
                            "content": "3案比較の詳細分析"
                        })
                        results_list.append({
                            "type": "document",
                            "name": task.get("name"),
                            "document_id": doc_result.get("document_id"),
                            "title": doc_result.get("title"),
                            "download_url": doc_result.get("download_url"),
                            "view_url": doc_result.get("view_url"),
                            "edit_url": doc_result.get("edit_url"),
                            "document_type": doc_result.get("document_type")
                        })
                        
                elif task.get("type") == "notification":
                    # 通知結果
                    recipients = task_result.get("recipients", 8) if task_result else 8
                    results_list.append({
                        "type": "notification",
                        "name": task.get("name"),
                        "recipients": recipients
                    })
                elif task.get("type") == "research":
                    # リサーチ結果
                    research_data = task_result.get("data") if task_result else workspace_service.research_market_data("ARPU動向")
                    results_list.append({
                        "type": "research",
                        "name": task.get("name"),
                        "data": research_data
                    })
                elif task.get("type") == "analysis":
                    # 分析結果
                    analysis_data = task_result.get("data") if task_result else workspace_service.analyze_data({})
                    results_list.append({
                        "type": "analysis",
                        "name": task.get("name"),
                        "data": analysis_data
                    })
        
        # メインのダウンロードURL（最初のドキュメント）
        main_doc = next((r for r in results_list if r.get("type") == "document"), None)
        if main_doc:
            # view_urlを優先、なければdownload_url
            download_url = main_doc.get("view_url") or main_doc.get("download_url") or main_doc.get("edit_url")
        else:
            download_url = "https://drive.google.com/file/d/mock_file_id/view"
        
        results = {
            "execution_id": execution_id,
            "results": results_list,
            "download_url": download_url
        }
        
        logger.info(f"Execution results retrieved for {execution_id}: {len(results_list)} results")
        
        return results
    except HelmException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_execution_results: {e}", exc_info=True)
        raise

@app.get("/api/download/{file_id}")
async def download_file(file_id: str):
    """ファイルダウンロードURL取得"""
    try:
        logger.info(f"Download file request: {file_id}")
        # Google Driveサービスを使用してダウンロードURLを取得
        try:
            download_url = drive_service.get_file_download_url(file_id)
        except Exception as e:
            logger.error(f"Failed to get download URL for file {file_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"ダウンロードURLの取得に失敗しました: {str(e)}",
                service_name="GoogleDriveService",
                details={"file_id": file_id}
            )
        
        # モック: ファイル情報を返す
        return {
            "file_id": file_id,
            "download_url": download_url,
            "filename": f"file_{file_id}.pdf" if not file_id.startswith("mock_") else "3案比較資料.pdf"
        }
    except HelmException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in download_file: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

