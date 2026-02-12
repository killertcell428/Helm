"""
Helm Backend API - Main Application
Google Meet → 議事録・チャット取得 → 重要性・緊急性評価 → 
人が承認/指示 → Googleサービス経由でリサーチ・分析・資料作成 → 
結果をアプリに返してダウンロード → 次回会議へ
"""

from dotenv import load_dotenv
import os
load_dotenv()  # .envファイルを読み込む

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from pydantic import BaseModel, ValidationError as PydanticValidationError
from typing import List, Optional, Dict, Any, Set
import uuid
import copy
from datetime import datetime
import traceback
import time
import asyncio
import json
from utils.logger import logger, set_log_context, clear_log_context
from utils.simple_cache import analysis_cache, execution_results_cache
from utils.error_notifier import error_notification_manager
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
    ScoringService,
    LLMService,
    MultiRoleLLMAnalyzer,
    EnsembleScoringService,
)
from services.agents.research_agent import execute_research_task
from services.agents.analysis_agent import execute_analysis_task
from services.agents.notification_agent import execute_notification_task
from services.agents.shared_context import SharedContext
from services.escalation_engine import EscalationEngine
# 拡張エスカレーションエンジン（エラーハンドリング付きでインポート）
try:
    from services.escalation_engine_enhanced import EnhancedEscalationEngine
    ENHANCED_ESCALATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"EnhancedEscalationEngine not available: {e}, using legacy engine")
    ENHANCED_ESCALATION_AVAILABLE = False
    EnhancedEscalationEngine = None

# データマスキングサービス（エラーハンドリング付きでインポート）
try:
    from services.data_masking import DataMaskingService
    DATA_MASKING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"DataMaskingService not available: {e}")
    DATA_MASKING_AVAILABLE = False
    DataMaskingService = None

# 監査ログサービス（エラーハンドリング付きでインポート）
try:
    from services.audit_log import AuditLogService, AuditAction
    AUDIT_LOG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AuditLogService not available: {e}")
    AUDIT_LOG_AVAILABLE = False
    AuditLogService = None
    AuditAction = None
from services.output_service import OutputService
from services.evaluation_metrics import EvaluationMetrics

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


# ==================== リクエストロギングミドルウェア ====================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """リクエストロギングとパフォーマンス計測のミドルウェア"""
    
    async def dispatch(self, request: Request, call_next):
        # リクエストIDの生成
        request_id = str(uuid.uuid4())
        
        # ログコンテキストの設定
        set_log_context(
            request_id=request_id,
            endpoint=request.url.path,
            method=request.method
        )
        
        # リクエスト開始時刻
        start_time = time.time()
        
        # リクエスト情報のログ
        client_host = request.client.host if request.client else "unknown"
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "extra_data": {
                    "request_id": request_id,
                    "client_host": client_host,
                    "query_params": dict(request.query_params),
                    "request_size": request.headers.get("content-length", "0")
                }
            }
        )
        
        try:
            # リクエストの処理
            response = await call_next(request)
            
            # 処理時間の計算
            process_time = time.time() - start_time
            
            # レスポンス情報のログ
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "extra_data": {
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "process_time": f"{process_time:.3f}s",
                        "response_size": response.headers.get("content-length", "unknown")
                    }
                }
            )
            
            # パフォーマンスログ（1秒以上かかった場合）
            if process_time > 1.0:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} took {process_time:.3f}s",
                    extra={
                        "extra_data": {
                            "request_id": request_id,
                            "process_time": f"{process_time:.3f}s",
                            "threshold": "1.0s"
                        }
                    }
                )
            
            # レスポンスヘッダーにリクエストIDを追加
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # エラー発生時のログ
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "extra_data": {
                        "request_id": request_id,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "process_time": f"{process_time:.3f}s",
                        "traceback": traceback.format_exc()
                    }
                }
            )
            raise
        finally:
            # ログコンテキストのクリア
            clear_log_context()


# リクエストロギングミドルウェアの追加
app.add_middleware(RequestLoggingMiddleware)

# ==================== グローバルエラーハンドラー ====================

@app.exception_handler(HelmException)
async def helm_exception_handler(request: Request, exc: HelmException):
    """Helmカスタム例外のハンドラー"""
    error_id = str(uuid.uuid4())
    request_id = request.headers.get("X-Request-ID") or "unknown"
    
    error_data = {
        "error_id": error_id,
        "request_id": request_id,
        "error_code": exc.error_code,
        "message": exc.message,
        "details": exc.details,
        "endpoint": request.url.path,
        "method": request.method,
        "client_host": request.client.host if request.client else "unknown",
        "timestamp": datetime.now().isoformat(),
        "traceback": traceback.format_exc()
    }
    
    logger.error(
        f"Error {error_id}: {exc.error_code} - {exc.message}",
        extra={"extra_data": error_data},
        exc_info=True
    )
    
    # エラー通知の送信
    error_notification_manager.notify_error(error_data)
    
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
    request_id = request.headers.get("X-Request-ID") or "unknown"
    errors = exc.errors()
    
    logger.warning(
        f"Validation error {error_id}: {errors}",
        extra={
            "extra_data": {
                "error_id": error_id,
                "request_id": request_id,
                "errors": errors,
                "endpoint": request.url.path,
                "method": request.method,
                "client_host": request.client.host if request.client else "unknown"
            }
        }
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
    request_id = request.headers.get("X-Request-ID") or "unknown"
    
    logger.warning(
        f"HTTP error {error_id}: {exc.status_code} - {exc.detail}",
        extra={
            "extra_data": {
                "error_id": error_id,
                "request_id": request_id,
                "status_code": exc.status_code,
                "endpoint": request.url.path,
                "method": request.method,
                "client_host": request.client.host if request.client else "unknown"
            }
        }
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
    request_id = request.headers.get("X-Request-ID") or "unknown"
    
    error_data = {
        "error_id": error_id,
        "request_id": request_id,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "endpoint": request.url.path,
        "method": request.method,
        "client_host": request.client.host if request.client else "unknown",
        "timestamp": datetime.now().isoformat(),
        "traceback": traceback.format_exc()
    }
    
    logger.error(
        f"Unhandled error {error_id}: {str(exc)}",
        exc_info=True,
        extra={"extra_data": error_data}
    )
    
    # エラー通知の送信
    error_notification_manager.notify_error(error_data)
    
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

class MaterialIngestRequest(BaseModel):
    material_id: str
    content: str
    metadata: Dict[str, Any]

class AnalyzeRequest(BaseModel):
    meeting_id: str
    chat_id: Optional[str] = None
    material_id: Optional[str] = None

class EscalateRequest(BaseModel):
    analysis_id: str

class ApproveRequest(BaseModel):
    escalation_id: str
    decision: str  # "approve" or "modify"
    modifications: Optional[Dict[str, Any]] = None

class ExecuteRequest(BaseModel):
    approval_id: str


class FalsePositiveFeedbackRequest(BaseModel):
    """誤検知フィードバック用リクエスト"""
    analysis_id: str
    pattern_id: str
    reason: str
    mitigation: Optional[str] = None

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
    scoring_service=scoring_service,
)  # ルールベース分析 + スコアリング
# エスカレーション判断エンジン（拡張機能を優先、エラー時は既存機能にフォールバック）
try:
    if ENHANCED_ESCALATION_AVAILABLE and EnhancedEscalationEngine:
        escalation_engine = EnhancedEscalationEngine(
            escalation_threshold=config.ESCALATION_THRESHOLD,
            use_enhanced_features=True
        )
        logger.info("Using EnhancedEscalationEngine with advanced features")
    else:
        escalation_engine = EscalationEngine(escalation_threshold=config.ESCALATION_THRESHOLD)
        logger.info("Using legacy EscalationEngine")
except Exception as e:
    logger.error(f"Failed to initialize escalation engine: {e}, using legacy engine", exc_info=True)
    escalation_engine = EscalationEngine(escalation_threshold=config.ESCALATION_THRESHOLD)

# データマスキングサービス（エラーハンドリング付きで初期化）
data_masking_service = None
if DATA_MASKING_AVAILABLE and DataMaskingService:
    try:
        data_masking_service = DataMaskingService()
        logger.info("DataMaskingService initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize DataMaskingService: {e}")
        data_masking_service = None

# 監査ログサービス（エラーハンドリング付きで初期化）
audit_log_service = None
if AUDIT_LOG_AVAILABLE and AuditLogService:
    try:
        audit_log_service = AuditLogService()
        logger.info("AuditLogService initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize AuditLogService: {e}")
        audit_log_service = None
workspace_service = GoogleWorkspaceService(
    credentials_path=config.GOOGLE_APPLICATION_CREDENTIALS,
    folder_id=config.GOOGLE_DRIVE_FOLDER_ID
)  # 環境変数から認証情報を取得（サービスアカウントまたはOAuth）
drive_service = GoogleDriveService(
    credentials_path=config.GOOGLE_APPLICATION_CREDENTIALS,
    shared_drive_id=config.GOOGLE_DRIVE_SHARED_DRIVE_ID,
    folder_id=config.GOOGLE_DRIVE_FOLDER_ID
)  # 環境変数から認証情報を取得（サービスアカウントまたはOAuth）
llm_service = LLMService()  # LLM統合サービス
multi_view_analyzer = MultiRoleLLMAnalyzer(llm_service=llm_service)  # マルチ視点LLM分析
ensemble_scoring_service = EnsembleScoringService()  # アンサンブルスコアリング
output_service = OutputService(output_dir=os.getenv("OUTPUT_DIR", "outputs"))  # 出力サービス
evaluation_metrics = EvaluationMetrics(data_dir=os.getenv("EVALUATION_DATA_DIR", "data/evaluation"))

# ==================== インメモリストレージ（開発用） ====================

meetings_db: Dict[str, Dict] = {}
chats_db: Dict[str, Dict] = {}
materials_db: Dict[str, Dict] = {}  # 会議資料データベース
analyses_db: Dict[str, Dict] = {}
escalations_db: Dict[str, Dict] = {}
approvals_db: Dict[str, Dict] = {}
executions_db: Dict[str, Dict] = {}

# グローバル共有コンテキスト（実行IDごとに管理）
shared_contexts: Dict[str, SharedContext] = {}

# ==================== WebSocket接続管理 ====================

# アクティブなWebSocket接続を管理: {execution_id: [WebSocket, ...]}
active_websocket_connections: Dict[str, List[WebSocket]] = {}

# 実行中のバックグラウンドタスク: {execution_id: asyncio.Task}
running_execution_tasks: Dict[str, asyncio.Task] = {}

# ==================== WebSocket接続管理ヘルパー ====================

async def add_websocket_connection(execution_id: str, websocket: WebSocket):
    """WebSocket接続を追加"""
    if execution_id not in active_websocket_connections:
        active_websocket_connections[execution_id] = []
    active_websocket_connections[execution_id].append(websocket)
    logger.info(f"WebSocket connection added for execution {execution_id} (total: {len(active_websocket_connections[execution_id])})")

async def remove_websocket_connection(execution_id: str, websocket: WebSocket):
    """WebSocket接続を削除"""
    if execution_id in active_websocket_connections:
        if websocket in active_websocket_connections[execution_id]:
            active_websocket_connections[execution_id].remove(websocket)
        if len(active_websocket_connections[execution_id]) == 0:
            del active_websocket_connections[execution_id]
    logger.info(f"WebSocket connection removed for execution {execution_id}")

async def broadcast_to_websockets(execution_id: str, message: Dict[str, Any]):
    """指定されたexecution_idのすべてのWebSocket接続にメッセージをブロードキャスト"""
    if execution_id not in active_websocket_connections:
        return
    
    disconnected = []
    
    for websocket in active_websocket_connections[execution_id]:
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send message to WebSocket: {e}")
            disconnected.append(websocket)
    
    # 切断された接続を削除
    for websocket in disconnected:
        await remove_websocket_connection(execution_id, websocket)

def generate_document_content(analysis: Optional[Dict[str, Any]], approval: Optional[Dict[str, Any]] = None) -> str:
    """
    分析結果からドキュメント内容を生成
    
    Args:
        analysis: 分析結果データ
        approval: 承認データ（オプション）
        
    Returns:
        生成されたドキュメント内容（マークダウン形式）
    """
    if not analysis:
        return "# 構造的問題分析結果\n\n分析データがありません。\n"
    
    content_text = "# 構造的問題分析結果\n\n"
    
    # 概要セクション
    content_text += "## 概要\n\n"
    content_text += f"- **総合スコア**: {analysis.get('score', 'N/A')}\n"
    content_text += f"- **重要度**: {analysis.get('severity', 'N/A')}\n"
    if analysis.get('urgency'):
        content_text += f"- **緊急性**: {analysis.get('urgency', 'N/A')}\n"
    if analysis.get('explanation'):
        content_text += f"\n**説明**: {analysis.get('explanation', '')}\n"
    content_text += "\n"
    
    # 分析結果の詳細
    findings = analysis.get("findings", [])
    if findings:
        content_text += "## 検出された問題\n\n"
        
        for i, finding in enumerate(findings, 1):
            content_text += f"### {i}. {finding.get('pattern_id', '問題')}\n\n"
            
            # 重要度と緊急性
            severity = finding.get('severity', 'N/A')
            urgency = finding.get('urgency', 'N/A')
            score = finding.get('score', 'N/A')
            
            content_text += f"**重要度**: {severity}  "
            content_text += f"**緊急性**: {urgency}  "
            content_text += f"**スコア**: {score}\n\n"
            
            # 説明
            description = finding.get('description', '')
            if description:
                content_text += f"{description}\n\n"
            
            # 証拠
            evidence = finding.get('evidence', [])
            if evidence:
                content_text += "**証拠**:\n"
                for ev in evidence:
                    content_text += f"- {ev}\n"
                content_text += "\n"
            
            # 評価詳細（存在する場合）
            evaluation = finding.get('evaluation')
            if evaluation:
                content_text += "**評価詳細**:\n"
                if isinstance(evaluation, dict):
                    overall_score = evaluation.get('overall_score', 'N/A')
                    importance_score = evaluation.get('importance_score', 'N/A')
                    urgency_score = evaluation.get('urgency_score', 'N/A')
                    reasons = evaluation.get('reasons', [])
                    
                    content_text += f"- 総合スコア: {overall_score}\n"
                    content_text += f"- 重要度スコア: {importance_score}\n"
                    content_text += f"- 緊急性スコア: {urgency_score}\n"
                    
                    if reasons:
                        content_text += "\n**理由**:\n"
                        for reason in reasons:
                            content_text += f"- {reason}\n"
                        content_text += "\n"
                content_text += "\n"
            
            # 定量スコア（存在する場合）
            quantitative_scores = finding.get('quantitative_scores')
            if quantitative_scores and isinstance(quantitative_scores, dict):
                content_text += "**定量スコア**:\n"
                for key, value in quantitative_scores.items():
                    content_text += f"- {key}: {value}\n"
                content_text += "\n"
    else:
        content_text += "検出された問題はありません。\n\n"
    
    # 推奨事項（承認データがある場合）
    if approval:
        decision = approval.get('decision', '')
        modifications = approval.get('modifications')
        
        if decision or modifications:
            content_text += "## Executive承認内容\n\n"
            if decision:
                content_text += f"**決定**: {decision}\n\n"
            if modifications:
                if isinstance(modifications, dict):
                    interventions = modifications.get('interventions') or modifications.get('approved_items')
                    if interventions:
                        content_text += "**承認された介入案**:\n"
                        for intervention in interventions:
                            content_text += f"- {intervention}\n"
                        content_text += "\n"
                elif isinstance(modifications, list):
                    content_text += "**修正内容**:\n"
                    for mod in modifications:
                        content_text += f"- {mod}\n"
                    content_text += "\n"
                elif isinstance(modifications, str):
                    content_text += f"**修正内容**: {modifications}\n\n"
    
    return content_text

async def execute_task(task: Dict[str, Any], execution: Dict[str, Any]) -> Dict[str, Any]:
    """個別のタスクを実行（ADKエージェントを使用）"""
    task_copy = task.copy() if isinstance(task, dict) else dict(task)
    execution_id = execution.get("execution_id")
    
    # 実行IDごとの共有コンテキストを取得または作成
    if execution_id not in shared_contexts:
        shared_contexts[execution_id] = SharedContext()
    context = shared_contexts[execution_id]
    
    try:
        task_type = task_copy.get("type")
        
        if task_type == "research":
            # ResearchAgentを実行
            result = await execute_research_task(task_copy, context.get_context())
            task_copy["result"] = result
        elif task_type == "analysis":
            # AnalysisAgentを実行
            result = await execute_analysis_task(task_copy, context.get_context())
            task_copy["result"] = result
        elif task_type == "notification":
            # NotificationAgentを実行
            result = await execute_notification_task(task_copy, context.get_context())
            task_copy["result"] = result
        elif task_type == "document":
            # 既存の実装を使用（Google Docs生成）
            approval = approvals_db.get(execution.get("approval_id"))
            escalation = None
            analysis = None
            if approval:
                escalation = escalations_db.get(approval.get("escalation_id"))
                if escalation:
                    analysis = analyses_db.get(escalation.get("analysis_id"))
            
            # 分析結果から資料内容を生成（改善版）
            content_text = generate_document_content(analysis, approval)
            
            doc_result = workspace_service.generate_document({
                "title": task_copy.get("name", "3案比較資料"),
                "content": content_text
            })
            
            task_copy["result"] = {
                "document_id": doc_result.get("document_id"),
                "title": doc_result.get("title"),
                "download_url": doc_result.get("download_url"),
                "view_url": doc_result.get("view_url"),
                "edit_url": doc_result.get("edit_url"),
                "document_type": doc_result.get("document_type")
            }
            logger.info(f"Document generated: {doc_result.get('document_id')} - {doc_result.get('title')}")
        # calendarタイプは未実装
        
        # 結果を共有コンテキストに保存
        context.save_result(task_copy.get("id"), task_copy.get("result", {}))
        task_copy["status"] = "completed"
    except Exception as e:
        logger.error(f"Task execution failed: {task_copy.get('name')} - {e}", exc_info=True)
        task_copy["status"] = "failed"
        task_copy["error"] = str(e)
    
    return task_copy

async def execute_tasks_background(execution_id: str):
    """バックグラウンドでタスクを実行し、進捗をWebSocket経由で送信"""
    try:
        execution = executions_db.get(execution_id)
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return
        
        tasks = execution.get("tasks", [])
        if not tasks:
            logger.warning(f"No tasks to execute for {execution_id}")
            return
        
        # 初期状態を送信
        await broadcast_to_websockets(execution_id, {
            "type": "progress",
            "data": {
                "execution_id": execution_id,
                "status": "running",
                "progress": 0,
                "tasks": tasks
            }
        })
        
        # 各タスクを順次実行（2秒間隔）
        updated_tasks = []
        for i, task in enumerate(tasks):
            # タスクを実行中に更新
            task["status"] = "running"
            await broadcast_to_websockets(execution_id, {
                "type": "progress",
                "data": {
                    "execution_id": execution_id,
                    "status": "running",
                    "progress": int((i / len(tasks)) * 100),
                    "tasks": tasks[:i] + [task] + tasks[i+1:]
                }
            })
            
            # タスクを実行（2秒待機）
            await asyncio.sleep(2)
            
            # タスクを実行
            executed_task = await execute_task(task, execution)
            updated_tasks.append(executed_task)
            
            # 進捗を更新
            progress = int(((i + 1) / len(tasks)) * 100)
            execution["progress"] = progress
            execution["updated_at"] = datetime.now().isoformat()
            execution["tasks"] = updated_tasks + tasks[i+1:]
            executions_db[execution_id] = execution
            
            # 進捗をブロードキャスト
            await broadcast_to_websockets(execution_id, {
                "type": "progress",
                "data": {
                    "execution_id": execution_id,
                    "status": "running",
                    "progress": progress,
                    "tasks": updated_tasks + tasks[i+1:]
                }
            })
        
        # すべてのタスクが完了
        execution["status"] = "completed"
        execution["progress"] = 100
        execution["updated_at"] = datetime.now().isoformat()
        execution["tasks"] = updated_tasks
        executions_db[execution_id] = execution
        
        # 完了通知を送信
        await broadcast_to_websockets(execution_id, {
            "type": "completed",
            "data": {
                "execution_id": execution_id,
                "status": "completed",
                "progress": 100,
                "tasks": updated_tasks
            }
        })
        
        # バックグラウンドタスクを削除
        if execution_id in running_execution_tasks:
            del running_execution_tasks[execution_id]
        
        logger.info(f"Execution {execution_id} completed")
        
    except Exception as e:
        logger.error(f"Error in background task execution for {execution_id}: {e}", exc_info=True)
        
        # エラー通知を送信
        await broadcast_to_websockets(execution_id, {
            "type": "error",
            "data": {
                "execution_id": execution_id,
                "message": str(e),
                "error_code": "EXECUTION_ERROR"
            }
        })
        
        # 実行状態を更新
        execution = executions_db.get(execution_id)
        if execution:
            execution["status"] = "failed"
            executions_db[execution_id] = execution
        
        # バックグラウンドタスクを削除
        if execution_id in running_execution_tasks:
            del running_execution_tasks[execution_id]

# ==================== APIエンドポイント ====================

@app.get("/")
async def root():
    """ヘルスチェック。Cache-Control で短時間キャッシュ可能（負荷軽減）。"""
    return JSONResponse(
        content={
            "message": "Helm API",
            "version": "0.1.0",
            "status": "running"
        },
        headers={"Cache-Control": "public, max-age=5"}
    )

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
        
        # データマスキング（エラーハンドリング付き）
        masked_meeting_data = {
            "meeting_id": request.meeting_id,
            "transcript": transcript,
            "parsed_data": parsed_data,
            "metadata": metadata,
            "ingested_at": datetime.now().isoformat(),
            "status": "ingested"
        }
        
        if data_masking_service:
            try:
                masked_meeting_data = data_masking_service.mask_meeting_data(masked_meeting_data)
                logger.info(f"Meeting data masked for {request.meeting_id}")
            except Exception as e:
                logger.warning(f"Failed to mask meeting data: {e}, using unmasked data")
                # エラー時はマスキングなしで続行
        
        meetings_db[request.meeting_id] = masked_meeting_data
        
        # 監査ログの記録（エラーハンドリング付き）
        if audit_log_service and AuditAction:
            try:
                # ユーザーIDとロールはリクエストから取得（デフォルト値を使用）
                user_id = request.headers.get("X-User-ID", "system")
                role = request.headers.get("X-User-Role", "system")
                client_host = request.client.host if request.client else None
                
                audit_log_service.log(
                    user_id=user_id,
                    role=role,
                    action=AuditAction.VIEW_MEETING,
                    resource_type="meeting",
                    resource_id=request.meeting_id,
                    ip_address=client_host,
                    details={"action": "ingest"}
                )
            except Exception as e:
                logger.warning(f"Failed to log audit: {e}")
                # エラー時はログ記録をスキップして続行
        
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
        
        # データマスキング（エラーハンドリング付き）
        masked_chat_data = {
            "chat_id": request.chat_id,
            "messages": messages,
            "parsed_data": parsed_data,
            "metadata": metadata,
            "ingested_at": datetime.now().isoformat(),
            "status": "ingested"
        }
        
        if data_masking_service:
            try:
                masked_chat_data = data_masking_service.mask_chat_data(masked_chat_data)
                logger.info(f"Chat data masked for {request.chat_id}")
            except Exception as e:
                logger.warning(f"Failed to mask chat data: {e}, using unmasked data")
                # エラー時はマスキングなしで続行
        
        chats_db[request.chat_id] = masked_chat_data
        
        # 監査ログの記録（エラーハンドリング付き）
        if audit_log_service and AuditAction:
            try:
                # ユーザーIDとロールはリクエストから取得（デフォルト値を使用）
                user_id = request.headers.get("X-User-ID", "system")
                role = request.headers.get("X-User-Role", "system")
                client_host = request.client.host if request.client else None
                
                audit_log_service.log(
                    user_id=user_id,
                    role=role,
                    action=AuditAction.VIEW_CHAT,
                    resource_type="chat",
                    resource_id=request.chat_id,
                    ip_address=client_host,
                    details={"action": "ingest"}
                )
            except Exception as e:
                logger.warning(f"Failed to log audit: {e}")
                # エラー時はログ記録をスキップして続行
        
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

@app.post("/api/materials/ingest")
async def ingest_material(request: MaterialIngestRequest):
    """会議資料の取り込み"""
    try:
        logger.info(f"Material ingest request: {request.material_id}")
        
        material_data = {
            "material_id": request.material_id,
            "content": request.content,
            "metadata": request.metadata,
            "ingested_at": datetime.now().isoformat(),
            "status": "ingested"
        }
        materials_db[request.material_id] = material_data
        
        logger.info(f"Material {request.material_id} ingested successfully")
        
        return {
            "material_id": request.material_id,
            "status": "success",
            "content_length": len(request.content),
            "metadata": request.metadata
        }
    except HelmException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ingest_material: {e}", exc_info=True)
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
        
        # 会議資料データを取得
        material = materials_db.get(request.material_id) if request.material_id else None
        if request.material_id and not material:
            logger.warning(f"Material {request.material_id} not found, proceeding without material data")
        
        # 構造的問題検知を実行（ルールベース + マルチ視点LLMのアンサンブル）
        try:
            meeting_parsed = meeting.get("parsed_data", {}) or {}
            # 生データも含める（LLMがテキストを直接分析できるように）
            if not meeting_parsed.get("transcript") and meeting.get("transcript"):
                meeting_parsed["transcript"] = meeting.get("transcript")
            
            chat_parsed = chat.get("parsed_data", {}) if chat else None
            # 生データも含める
            if chat and not (chat_parsed or {}).get("messages") and chat.get("messages"):
                if not chat_parsed:
                    chat_parsed = {}
                chat_parsed["messages"] = chat.get("messages")
            
            material_data = material if material else None
            
            # ルールベース分析（常に実行し、安全側のベースラインとする）
            # use_vertex_ai=False なので、analyze() は _analyze_with_rules を呼ぶ
            rule_result = analyzer.analyze(meeting_parsed, chat_parsed)
            
            # マルチ視点LLM分析（LLM利用可否は内部で判定）
            multi_view_results = multi_view_analyzer.analyze_with_roles(
                meeting_data=meeting_parsed,
                chat_data=chat_parsed,
                materials_data=material_data,
            )
            
            # アンサンブルスコアリング
            ensemble_result = ensemble_scoring_service.combine(
                rule_result=rule_result,
                role_results=multi_view_results,
            )
        except ServiceError:
            # ServiceErrorはそのまま再スロー
            raise
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"Failed to analyze: {e}",
                extra={
                    "error_type": error_type,
                    "meeting_id": request.meeting_id,
                    "chat_id": request.chat_id,
                    "material_id": request.material_id
                },
                exc_info=True
            )
            raise ServiceError(
                message=f"構造的問題検知に失敗しました: {str(e)}",
                service_name="AnalysisEnsemble",
                details={
                    "meeting_id": request.meeting_id,
                    "chat_id": request.chat_id,
                    "material_id": request.material_id,
                    "error_type": error_type
                }
            )
        
        # 説明文に根拠引用を追加（エラーハンドリング付き）
        explanation = ensemble_result.get("explanation", "")
        findings = ensemble_result.get("findings", [])
        
        # 根拠引用サービスを使用（エラーハンドリング付き）
        try:
            if EVIDENCE_CITATION_AVAILABLE:
                from services.evidence_citation import EvidenceCitationService
                evidence_service = EvidenceCitationService()
                explanation = evidence_service.add_evidence_citations(
                    explanation,
                    findings,
                    meeting_parsed,
                    chat_parsed
                )
                logger.info(f"Evidence citations added to explanation for analysis {analysis_id}")
        except Exception as e:
            logger.warning(f"Failed to add evidence citations: {e}, using original explanation")
            # エラー時は元の説明文を使用（フォールバック）
        
        analysis_data = {
            "analysis_id": analysis_id,
            "meeting_id": request.meeting_id,
            "chat_id": request.chat_id,
            # アンサンブル結果をトップレベルに反映
            "findings": findings,
            "scores": rule_result.get("scores", {}),
            "score": ensemble_result.get("overall_score", 0),
            "overall_score": ensemble_result.get("overall_score", 0),  # 拡張エスカレーション用
            "severity": ensemble_result.get("severity", "MEDIUM"),
            "urgency": ensemble_result.get("urgency", "MEDIUM"),
            "explanation": explanation,  # 根拠引用付きの説明文
            "created_at": rule_result.get("created_at", datetime.now().isoformat()),
            "status": "completed",
            # LLM生成かモックかを明示（マルチロール結果が1つでもあればLLM利用とみなす）
            "is_llm_generated": len(multi_view_results) > 0,
            "llm_status": "success" if len(multi_view_results) > 0 else "disabled",
            "llm_model": llm_service.model_name if len(multi_view_results) > 0 else None,
            # 追加メタ情報
            "multi_view": multi_view_results,
            "ensemble": {
                "overall_score": ensemble_result.get("overall_score", 0),
                "severity": ensemble_result.get("severity", "MEDIUM"),
                "urgency": ensemble_result.get("urgency", "MEDIUM"),
                "reasons": ensemble_result.get("reasons", []),
                "contributing_roles": ensemble_result.get("contributing_roles", []),
            },
            # ルールベースとLLMスコア（確信度計算用）
            "rule_score": rule_result.get("overall_score", 0),
            "llm_score": sum(r.get("overall_score", 0) * r.get("weight", 0) for r in multi_view_results) / max(sum(r.get("weight", 0) for r in multi_view_results), 1) if multi_view_results else 0,
        }
        
        analyses_db[analysis_id] = analysis_data
        
        # 分析結果をJSONファイルに出力
        try:
            # アンサンブル結果を保存用の形式に変換
            output_data = {
                "findings": ensemble_result.get("findings", []),
                "overall_score": ensemble_result.get("overall_score", 0),
                "severity": ensemble_result.get("severity", "MEDIUM"),
                "urgency": ensemble_result.get("urgency", "MEDIUM"),
                "explanation": ensemble_result.get("explanation", ""),
                "created_at": rule_result.get("created_at", datetime.now().isoformat()),
                "multi_view": multi_view_results,
                "ensemble": ensemble_result,
            }
            output_file_info = output_service.save_analysis_result(analysis_id, output_data)
            analysis_data["output_file"] = output_file_info
            # LogRecordの予約キーである"filename"はextraで上書きできないため、別キー名を使用する
            logger.info(
                f"Analysis result saved to file: {output_file_info.get('filename')}",
                extra={
                    "analysis_id": analysis_id,
                    "output_filename": output_file_info.get("filename")
                }
            )
        except Exception as e:
            error_type = type(e).__name__
            logger.warning(
                f"Failed to save analysis result to file: {e}",
                extra={
                    "error_type": error_type,
                    "analysis_id": analysis_id
                },
                exc_info=True
            )
            # ファイル保存失敗は分析結果の返却には影響しない
        
        logger.info(f"Analysis {analysis_id} completed: score={ensemble_result.get('overall_score', 0)}, severity={ensemble_result.get('severity', 'MEDIUM')}")
        
        # 監査ログの記録（エラーハンドリング付き）
        if audit_log_service and AuditAction:
            try:
                user_id = request.headers.get("X-User-ID", "system")
                role = request.headers.get("X-User-Role", "system")
                client_host = request.client.host if request.client else None
                
                audit_log_service.log(
                    user_id=user_id,
                    role=role,
                    action=AuditAction.VIEW_ANALYSIS,
                    resource_type="analysis",
                    resource_id=analysis_id,
                    ip_address=client_host,
                    details={"meeting_id": request.meeting_id, "chat_id": request.chat_id}
                )
            except Exception as e:
                logger.warning(f"Failed to log audit: {e}")
                # エラー時はログ記録をスキップして続行
        
        return analysis_data
    except HelmException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze: {e}", exc_info=True)
        raise

@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """分析結果取得（キャッシュ: 同一 analysis_id は TTL 間キャッシュ）"""
    try:
        cached = analysis_cache.get(analysis_id)
        if cached is not None:
            logger.debug(f"Get analysis cache hit: {analysis_id}")
            return cached
        logger.info(f"Get analysis request: {analysis_id}")
        analysis = analyses_db.get(analysis_id)
        if not analysis:
            raise NotFoundError(
                message=f"分析結果が見つかりません: {analysis_id}",
                resource_type="analysis",
                resource_id=analysis_id
            )
        analysis_cache.set(analysis_id, copy.deepcopy(analysis))
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
        
        # エスカレーション判断エンジンを使用（拡張機能を統合、エラーハンドリング付き）
        escalation_info = None
        try:
            # 拡張エスカレーションエンジンを使用（会議データとチャットデータを渡す）
            meeting = meetings_db.get(analysis.get("meeting_id"))
            chat = chats_db.get(analysis.get("chat_id")) if analysis.get("chat_id") else None
            
            escalation_info = escalation_engine.create_escalation(
                request.analysis_id,
                analysis,
                meeting,
                chat
            )
        except Exception as e:
            logger.error(f"Failed to create escalation: {e}", exc_info=True)
            # エラー時は既存のメソッドで再試行（フォールバック）
            try:
                if hasattr(escalation_engine, 'legacy_engine') and escalation_engine.legacy_engine:
                    escalation_info = escalation_engine.legacy_engine.create_escalation(request.analysis_id, analysis)
                elif hasattr(escalation_engine, 'create_escalation'):
                    # 拡張エンジンの基本メソッドを試行
                    escalation_info = escalation_engine.create_escalation(request.analysis_id, analysis)
            except Exception as e2:
                logger.error(f"Failed to create escalation with fallback: {e2}", exc_info=True)
                raise ServiceError(
                    message=f"エスカレーション判断に失敗しました: {str(e)}",
                    service_name="EscalationEngine",
                    details={"analysis_id": request.analysis_id}
                )
        
        if not escalation_info:
            # スコアと重要度を取得（analysis_dataの構造に対応）
            score = analysis.get("score", 0)
            if score == 0:
                ensemble = analysis.get("ensemble", {})
                if isinstance(ensemble, dict):
                    score = ensemble.get("overall_score", 0)
            severity = analysis.get("severity", "LOW")
            ensemble = analysis.get("ensemble", {})
            if isinstance(ensemble, dict) and not severity or severity == "LOW":
                severity = ensemble.get("severity", severity)
            
            raise ValidationError(
                message=f"エスカレーション条件を満たしていません（スコア: {score}点、重要度: {severity}）。健全な意思決定が行われている場合や、構造的問題が検出されていない場合はエスカレーションされません。",
                details={
                    "analysis_id": request.analysis_id,
                    "score": score,
                    "severity": severity,
                    "reason": "スコアが閾値未満、または構造的問題が検出されていません"
                }
            )
        
        escalation_id = str(uuid.uuid4())
        
        # エスカレーションデータを構築（拡張機能のフィールドも含める）
        escalation_data = {
            "escalation_id": escalation_id,
            "analysis_id": request.analysis_id,
            "target_role": escalation_info.get("target_role", escalation_info.get("target_roles", ["Executive"])[0] if isinstance(escalation_info.get("target_roles"), list) else "Executive"),
            "reason": escalation_info.get("reason", "構造的問題が検出されました。"),
            "severity": escalation_info.get("severity", "MEDIUM"),
            "urgency": escalation_info.get("urgency", "MEDIUM"),
            "score": escalation_info.get("score", 0),
            "created_at": escalation_info.get("created_at", datetime.now().isoformat()),
            "status": escalation_info.get("status", "pending")
        }
        
        # 拡張機能のフィールドを追加（存在する場合）
        if "stage" in escalation_info:
            escalation_data["stage"] = escalation_info["stage"]
        if "stage_name" in escalation_info:
            escalation_data["stage_name"] = escalation_info["stage_name"]
        if "target_roles" in escalation_info:
            escalation_data["target_roles"] = escalation_info["target_roles"]
        if "action_required" in escalation_info:
            escalation_data["action_required"] = escalation_info["action_required"]
        if "confidence" in escalation_info:
            escalation_data["confidence"] = escalation_info["confidence"]
        if "confidence_level" in escalation_info:
            escalation_data["confidence_level"] = escalation_info["confidence_level"]
        if "question" in escalation_info:
            escalation_data["question"] = escalation_info["question"]
        if "type" in escalation_info:
            escalation_data["type"] = escalation_info["type"]
        
        escalations_db[escalation_id] = escalation_data
        
        target_role = escalation_data.get("target_role", "Executive")
        logger.info(f"Escalation {escalation_id} created: target_role={target_role}")
        
        # 監査ログの記録（エラーハンドリング付き）
        if audit_log_service and AuditAction:
            try:
                user_id = request.headers.get("X-User-ID", "system")
                role = request.headers.get("X-User-Role", "system")
                client_host = request.client.host if request.client else None
                
                audit_log_service.log(
                    user_id=user_id,
                    role=role,
                    action=AuditAction.ESCALATE,
                    resource_type="escalation",
                    resource_id=escalation_id,
                    ip_address=client_host,
                    details={"analysis_id": request.analysis_id, "target_role": target_role}
                )
            except Exception as e:
                logger.warning(f"Failed to log audit: {e}")
                # エラー時はログ記録をスキップして続行
        
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
        
        # 分析結果と承認データを取得
        escalation = escalations_db.get(approval.get("escalation_id"))
        analysis = None
        if escalation:
            analysis = analyses_db.get(escalation.get("analysis_id"))
        
        # 承認された介入案を抽出
        approved_interventions = None
        if approval.get("modifications"):
            modifications = approval.get("modifications")
            if isinstance(modifications, dict):
                # modificationsから介入案を抽出
                approved_interventions = modifications.get("interventions") or modifications.get("approved_items")
            elif isinstance(modifications, list):
                approved_interventions = modifications
        
        # LLMサービスを使用してタスクを生成（フォールバックはLLMサービス内で処理）
        try:
            if analysis:
                task_generation_result = llm_service.generate_tasks(
                    analysis_result=analysis,
                    approval_data=approval,
                    approved_interventions=approved_interventions
                )
                
                # 生成されたタスクを実行計画に反映
                generated_tasks = task_generation_result.get("tasks", [])
                tasks = []
                for i, task_def in enumerate(generated_tasks, start=1):
                    tasks.append({
                        "id": task_def.get("id", f"task{i}"),
                        "name": task_def.get("name", ""),
                        "status": "pending",
                        "type": task_def.get("type", "research"),
                        "description": task_def.get("description", ""),
                        "dependencies": task_def.get("dependencies", []),
                        "estimated_duration": task_def.get("estimated_duration"),
                        "expected_output": task_def.get("expected_output")
                    })
            else:
                # 分析結果がない場合はモックタスクを使用
                logger.warning("Analysis result not found, using mock tasks")
                tasks = [
                    {"id": "task1", "name": "市場データ分析", "status": "pending", "type": "research"},
                    {"id": "task2", "name": "社内データ統合", "status": "pending", "type": "analysis"},
                    {"id": "task3", "name": "3案比較資料の自動生成", "status": "pending", "type": "document"},
                    {"id": "task4", "name": "関係部署への事前通知", "status": "pending", "type": "notification"},
                    {"id": "task5", "name": "会議アジェンダの更新", "status": "pending", "type": "calendar"}
                ]
        except ServiceError:
            # ServiceErrorはそのまま再スロー
            raise
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"Failed to generate tasks with LLM: {e}",
                extra={
                    "error_type": error_type,
                    "approval_id": request.approval_id,
                    "has_analysis": analysis is not None
                },
                exc_info=True
            )
            # エラー時はモックタスクにフォールバック
            logger.warning("Falling back to mock tasks due to LLM error")
            tasks = [
                {"id": "task1", "name": "市場データ分析", "status": "pending", "type": "research"},
                {"id": "task2", "name": "社内データ統合", "status": "pending", "type": "analysis"},
                {"id": "task3", "name": "3案比較資料の自動生成", "status": "pending", "type": "document"},
                {"id": "task4", "name": "関係部署への事前通知", "status": "pending", "type": "notification"},
                {"id": "task5", "name": "会議アジェンダの更新", "status": "pending", "type": "calendar"}
            ]
        
        # タスク生成結果からLLM生成かモックかを取得
        is_llm_generated = False
        llm_status = "unknown"
        llm_model = None
        if analysis:
            task_result = task_generation_result if 'task_generation_result' in locals() else None
            if task_result:
                is_llm_generated = not task_result.get("_is_mock", True)
                llm_status = task_result.get("_llm_status", "unknown")
                llm_model = task_result.get("_llm_model", None)
        
        execution_data = {
            "execution_id": execution_id,
            "approval_id": request.approval_id,
            "status": "running",
            "progress": 0,
            "tasks": tasks,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            # LLM生成かモックかを明示
            "is_llm_generated": is_llm_generated,
            "llm_status": llm_status,
            "llm_model": llm_model
        }
        
        executions_db[execution_id] = execution_data
        
        # タスク生成結果をJSONファイルに出力
        try:
            if analysis:
                # タスク生成結果を取得（LLM生成かモックかを含む）
                task_result_data = task_generation_result if 'task_generation_result' in locals() else {
                    "tasks": tasks,
                    "execution_plan": {
                        "total_tasks": len(tasks),
                        "estimated_total_duration": "未計算",
                        "critical_path": []
                    },
                    "_is_mock": True,
                    "_llm_status": "unknown"
                }
                
                task_result = {
                    "tasks": tasks,
                    "execution_plan": {
                        "total_tasks": len(tasks),
                        "estimated_total_duration": "未計算",
                        "critical_path": []
                    }
                }
                output_file_info = output_service.save_task_generation_result(execution_id, task_result_data)
                execution_data["output_file"] = output_file_info
                logger.info(
                    f"Task generation result saved to file: {output_file_info.get('filename')}",
                    extra={"execution_id": execution_id, "filename": output_file_info.get('filename')}
                )
        except Exception as e:
            error_type = type(e).__name__
            logger.warning(
                f"Failed to save task generation result to file: {e}",
                extra={
                    "error_type": error_type,
                    "execution_id": execution_id
                },
                exc_info=True
            )
            # ファイル保存失敗は実行開始には影響しない
        
        logger.info(f"Execution {execution_id} started: {len(tasks)} tasks")
        
        # バックグラウンドタスクとして実行を開始
        if execution_id not in running_execution_tasks:
            task = asyncio.create_task(execute_tasks_background(execution_id))
            running_execution_tasks[execution_id] = task
        
        return execution_data
    except HelmException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in execute: {e}", exc_info=True)
        raise

@app.websocket("/api/execution/{execution_id}/ws")
async def websocket_endpoint(websocket: WebSocket, execution_id: str):
    """WebSocketエンドポイント: 実行進捗のリアルタイム更新"""
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for execution {execution_id}")
    
    try:
        # 実行状態を確認
        execution = executions_db.get(execution_id)
        if not execution:
            await websocket.send_json({
                "type": "error",
                "data": {
                    "execution_id": execution_id,
                    "message": f"実行状態が見つかりません: {execution_id}",
                    "error_code": "NOT_FOUND"
                }
            })
            await websocket.close()
            return
        
        # WebSocket接続を追加
        await add_websocket_connection(execution_id, websocket)
        
        # 現在の実行状態を送信
        await websocket.send_json({
            "type": "progress",
            "data": {
                "execution_id": execution_id,
                "status": execution.get("status", "unknown"),
                "progress": execution.get("progress", 0),
                "tasks": execution.get("tasks", [])
            }
        })
        
        # バックグラウンドタスクが開始されていない場合は開始
        if execution.get("status") == "running" and execution_id not in running_execution_tasks:
            task = asyncio.create_task(execute_tasks_background(execution_id))
            running_execution_tasks[execution_id] = task
        
        # クライアントからのメッセージを待機
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "subscribe":
                    # 既に接続済みなので何もしない
                    pass
                elif message.get("type") == "unsubscribe":
                    break
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for execution {execution_id}")
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON message from WebSocket: {data}")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}", exc_info=True)
                
    except Exception as e:
        logger.error(f"Error in WebSocket endpoint: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "data": {
                    "execution_id": execution_id,
                    "message": str(e),
                    "error_code": "WEBSOCKET_ERROR"
                }
            })
        except:
            pass
    finally:
        # WebSocket接続を削除
        await remove_websocket_connection(execution_id, websocket)
        logger.info(f"WebSocket connection closed for execution {execution_id}")

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
                            
                            # 分析結果から資料内容を生成（改善版）
                            content_text = generate_document_content(analysis, approval)
                            
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
    """実行結果取得（完了済みは TTL 間キャッシュ）"""
    try:
        execution = executions_db.get(execution_id)
        if not execution:
            raise NotFoundError(
                message=f"実行状態が見つかりません: {execution_id}",
                resource_type="execution",
                resource_id=execution_id
            )
        if execution.get("status") == "completed":
            cached = execution_results_cache.get(execution_id)
            if cached is not None:
                logger.debug(f"Get execution results cache hit: {execution_id}")
                return cached
        logger.info(f"Get execution results request: {execution_id}")
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
        # 完了済み実行結果はキャッシュ（同一 execution_id の再取得を軽量化）
        if execution.get("status") == "completed":
            execution_results_cache.set(execution_id, copy.deepcopy(results))
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

@app.get("/api/outputs")
async def list_outputs(file_type: Optional[str] = None):
    """出力ファイル一覧取得"""
    try:
        logger.info(f"List outputs request: file_type={file_type}")
        files = output_service.list_files(file_type=file_type)
        return {
            "files": files,
            "total": len(files)
        }
    except HelmException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            f"Unexpected error in list_outputs: {e}",
            extra={
                "error_type": error_type,
                "file_type": file_type
            },
            exc_info=True
        )
        raise

@app.get("/api/outputs/{file_id}")
async def get_output_file(file_id: str):
    """出力ファイル取得（ダウンロード）"""
    try:
        logger.info(f"Get output file request: {file_id}")
        
        # ファイルを取得
        file_data = output_service.get_file(file_id)
        if not file_data:
            raise NotFoundError(
                message=f"出力ファイルが見つかりません: {file_id}",
                resource_type="output_file",
                resource_id=file_id
            )
        
        # ファイルパスを取得
        file_path = output_service.get_file_path(file_id)
        if not file_path:
            raise NotFoundError(
                message=f"出力ファイルが見つかりません: {file_id}",
                resource_type="output_file",
                resource_id=file_id
            )
        
        # ファイルを返す
        return FileResponse(
            path=str(file_path),
            filename=file_id,
            media_type="application/json"
        )
    except HelmException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            f"Unexpected error in get_output_file: {e}",
            extra={
                "error_type": error_type,
                "file_id": file_id
            },
            exc_info=True
        )
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

