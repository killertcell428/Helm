# Helm 開発者ガイド

このガイドは、Helmプロジェクトの開発に参加する開発者向けの詳細なドキュメントです。

## 目次

1. [セットアップガイド](#セットアップガイド)
2. [プロジェクト構造](#プロジェクト構造)
3. [開発ワークフロー](#開発ワークフロー)
4. [API開発ガイド](#api開発ガイド)
5. [データモデル](#データモデル)
6. [統合ガイド](#統合ガイド)
7. [テスト](#テスト)
8. [デバッグ](#デバッグ)

---

## セットアップガイド

### 環境構築

#### 必要なツール

- **Python 3.11以上** - [ダウンロード](https://www.python.org/downloads/)
- **Node.js 18以上** - [ダウンロード](https://nodejs.org/)
- **pnpm** - Node.jsのパッケージマネージャー
  ```bash
  npm install -g pnpm
  ```

#### バックエンドのセットアップ

1. **仮想環境の作成**
   ```bash
   cd Dev/backend
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

2. **依存関係のインストール**
   
   初回インストール時は、最小限の依存関係から始めることをおすすめします：
   ```bash
   # 最小限の依存関係（推奨・モックデータ使用時）
   pip install -r requirements_minimal.txt
   ```
   
   すべての依存関係（Google Cloudライブラリ含む）をインストールする場合：
   ```bash
   # すべての依存関係
   pip install -r requirements.txt
   ```
   
   **注意:** 
   - 現在はモックデータを使用しているため、`requirements_minimal.txt` で十分です
   - `requirements.txt` をインストールする場合、Google Cloudライブラリのインストールに時間がかかる場合があります
   - Windows環境で `pydantic-core` のインストールエラーが発生する場合は、`requirements_minimal.txt` を使用してください

3. **環境変数の設定**
   
   `.env` ファイルを作成して、必要な環境変数を設定します：
   ```bash
   # .env ファイルの例
   USE_LLM=true
   GOOGLE_CLOUD_PROJECT_ID=your-project-id
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
   OUTPUT_DIR=outputs
   ```
   
   **現在はモックデータを使用しているため、環境変数の設定は不要です。**

#### フロントエンドのセットアップ

1. **依存関係のインストール**
   ```bash
   cd Dev/app/v0-helm-demo
   pnpm install
   ```

2. **環境変数の設定**
   
   `.env.local` ファイルを作成します：
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

### Google Cloud認証情報の設定

実APIモードを使用する場合、Google Cloud認証情報の設定が必要です。

詳細は以下のドキュメントを参照してください：
- [個人アカウントでのセットアップ](./backend/QUICK_SETUP_PERSONAL_DRIVE.md)
- [Google Workspaceでのセットアップ](./backend/SETUP_SHARED_DRIVE.md)
- [Vertex AI設定](./backend/VERTEX_AI_SETUP.md)

### Vertex AI設定

LLM統合を使用する場合、Vertex AIの設定が必要です。

詳細は [Vertex AI設定ガイド](./backend/VERTEX_AI_SETUP.md) を参照してください。

---

## プロジェクト構造

### ディレクトリ構成

```
Dev/
├── app/
│   └── v0-helm-demo/          # フロントエンド（Next.js）
│       ├── app/               # Next.js App Router
│       │   ├── demo/          # デモページ
│       │   │   └── case1/     # Case1デモ
│       │   ├── layout.tsx     # レイアウト
│       │   └── page.tsx        # ホームページ
│       ├── components/        # Reactコンポーネント
│       │   └── ui/            # UIコンポーネント
│       ├── lib/               # ユーティリティ
│       │   └── api.ts         # APIクライアント
│       └── package.json
├── backend/                   # バックエンド（Python FastAPI）
│   ├── main.py               # メインAPI
│   ├── config.py              # 設定
│   ├── services/              # サービス層
│   │   ├── google_meet.py     # Google Meet統合
│   │   ├── google_chat.py     # Google Chat統合
│   │   ├── analyzer.py        # 構造的問題検知（ルールベース）
│   │   ├── llm_service.py     # LLM統合サービス
│   │   ├── vertex_ai.py       # Vertex AI統合
│   │   ├── google_workspace.py # Google Workspace統合
│   │   ├── google_drive.py    # Google Drive統合
│   │   ├── scoring.py          # スコアリングサービス
│   │   ├── escalation_engine.py # エスカレーション判断エンジン
│   │   └── output_service.py   # 出力サービス
│   ├── schemas/               # データスキーマ
│   │   └── firestore.py       # Firestoreスキーマ定義
│   ├── utils/                 # ユーティリティ
│   │   ├── logger.py          # ログ機能
│   │   ├── exceptions.py      # カスタム例外
│   │   └── error_notifier.py  # エラー通知
│   ├── tests/                 # テスト
│   │   ├── unit/              # ユニットテスト
│   │   ├── integration/      # 統合テスト
│   │   └── e2e/               # E2Eテスト
│   └── requirements.txt       # 依存関係
└── docs/                      # ドキュメント（将来）
```

### 主要ファイルの役割

#### バックエンド

- **`main.py`**: FastAPIアプリケーションのメインファイル。全APIエンドポイントの定義
- **`config.py`**: アプリケーション設定（CORS、APIタイトルなど）
- **`services/`**: ビジネスロジックを実装するサービス層
  - `google_meet.py`: Google Meet議事録の取得とパース
  - `google_chat.py`: Google Chatメッセージの取得とパース
  - `llm_service.py`: LLM統合（Vertex AI / Gemini）のラッパー
  - `scoring.py`: スコアリングロジック
  - `escalation_engine.py`: エスカレーション判断ロジック
- **`utils/`**: 共通ユーティリティ
  - `logger.py`: ログ機能（構造化ログ、リクエストID追跡）
  - `exceptions.py`: カスタム例外クラス
  - `error_notifier.py`: エラー通知機能

#### フロントエンド

- **`app/demo/case1/page.tsx`**: Case1デモページのメインコンポーネント
- **`lib/api.ts`**: APIクライアント（型定義、エラーハンドリング）

### コード規約・スタイルガイド

#### Python

- **フォーマッター**: Black（将来実装予定）
- **リンター**: flake8（将来実装予定）
- **型ヒント**: 可能な限り型ヒントを使用
- **docstring**: Googleスタイルのdocstringを使用

#### TypeScript

- **フォーマッター**: Prettier（将来実装予定）
- **リンター**: ESLint（将来実装予定）
- **型定義**: 厳密な型定義を使用

---

## 開発ワークフロー

### ローカル開発環境の起動

1. **バックエンドの起動**
   ```bash
   cd Dev/backend
   # 仮想環境を有効化
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   
   # サーバーを起動
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **フロントエンドの起動**
   ```bash
   cd Dev/app/v0-helm-demo
   pnpm dev
   ```

3. **動作確認**
   - バックエンド: http://localhost:8000/docs
   - フロントエンド: http://localhost:3000

### デバッグ方法

#### バックエンドのデバッグ

1. **ログの確認**
   - ログは標準出力に出力されます
   - リクエストIDが各ログに含まれているため、特定のリクエストを追跡できます

2. **デバッガーの使用**
   - VS Codeのデバッガーを使用できます
   - `.vscode/launch.json` に設定を追加（将来実装予定）

3. **APIドキュメントでのテスト**
   - http://localhost:8000/docs でSwagger UIを使用してAPIをテストできます

#### フロントエンドのデバッグ

1. **ブラウザの開発者ツール**
   - Chrome DevToolsを使用してデバッグできます
   - React DevToolsを使用してコンポーネントの状態を確認できます

2. **ログの確認**
   - コンソールログを確認できます
   - APIリクエスト/レスポンスはブラウザのNetworkタブで確認できます

### テストの実行

#### バックエンドのテスト

```bash
cd Dev/backend
# 仮想環境を有効化
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# テストを実行
pytest
```

#### フロントエンドのテスト

```bash
cd Dev/app/v0-helm-demo
pnpm test
```

### コード変更の反映

- **バックエンド**: `--reload` フラグにより、コード変更が自動的に反映されます
- **フロントエンド**: Next.jsのホットリロードにより、コード変更が自動的に反映されます

---

## API開発ガイド

### 新しいエンドポイントの追加

1. **リクエスト/レスポンスモデルの定義**
   
   `main.py` にPydanticモデルを追加：
   ```python
   class NewRequest(BaseModel):
       field1: str
       field2: Optional[int] = None
   ```

2. **エンドポイントの実装**
   
   `main.py` にエンドポイントを追加：
   ```python
   @app.post("/api/new-endpoint")
   async def new_endpoint(request: NewRequest):
       try:
           # ビジネスロジック
           return {"status": "success"}
       except HelmException:
           raise
       except Exception as e:
           logger.error(f"Unexpected error: {e}", exc_info=True)
           raise
   ```

3. **エラーハンドリング**
   
   - `HelmException` を継承したカスタム例外を使用
   - 適切なHTTPステータスコードを返す
   - エラーログを記録

4. **ドキュメントの更新**
   
   - `API_DOCUMENTATION.md` にエンドポイントの説明を追加
   - Swagger UIのdocstringを更新

### サービス層の実装パターン

1. **サービスクラスの作成**
   
   `services/` ディレクトリに新しいサービスファイルを作成：
   ```python
   class NewService:
       def __init__(self):
           # 初期化
           pass
       
       def method(self, param: str) -> Dict[str, Any]:
           # 実装
           return {}
   ```

2. **モックデータの提供**
   
   実APIが利用できない場合のフォールバック：
   ```python
   def get_data(self, id: str) -> Dict[str, Any]:
       try:
           # 実API呼び出し
           return real_api_call(id)
       except Exception:
           # モックデータにフォールバック
           return self._get_mock_data(id)
   ```

3. **エラーハンドリング**
   
   - `ServiceError` を適切に使用
   - リトライ可能なエラーは `RetryableError` を使用

### エラーハンドリングのベストプラクティス

1. **カスタム例外の使用**
   - `HelmException` を継承した例外を使用
   - 適切なエラーコードを設定

2. **エラーログの記録**
   - `logger.error()` を使用してエラーを記録
   - `exc_info=True` でスタックトレースを含める

3. **ユーザーフレンドリーなメッセージ**
   - エラーメッセージは日本語で、分かりやすく

4. **エラーIDの提供**
   - 各エラーに一意のIDを付与して、トラブルシューティングを容易に

### ログ出力の方法

```python
from utils.logger import logger

# 情報ログ
logger.info("処理が完了しました", extra={"extra_data": {"key": "value"}})

# 警告ログ
logger.warning("警告メッセージ")

# エラーログ
logger.error("エラーが発生しました", exc_info=True)
```

---

## データモデル

### 主要なデータ構造

#### MeetingIngestRequest
```python
{
    "meeting_id": str,
    "transcript": Optional[str],
    "metadata": Dict[str, Any]
}
```

#### ChatIngestRequest
```python
{
    "chat_id": str,
    "messages": Optional[List[Dict[str, Any]]],
    "metadata": Dict[str, Any]
}
```

#### AnalysisResult
```python
{
    "analysis_id": str,
    "meeting_id": str,
    "chat_id": Optional[str],
    "findings": List[Dict[str, Any]],
    "score": int,
    "severity": str,
    "explanation": str,
    "is_llm_generated": bool,
    "llm_status": str,
    "llm_model": Optional[str]
}
```

### Firestoreスキーマ（将来実装時）

詳細は `schemas/firestore.py` を参照してください。

---

## 統合ガイド

### Google API統合の方法

#### Google Meet API

1. **認証情報の設定**
   - Google Cloud Consoleでサービスアカウントを作成
   - 認証情報JSONファイルをダウンロード
   - `GOOGLE_APPLICATION_CREDENTIALS` 環境変数に設定

2. **サービスの実装**
   - `services/google_meet.py` を参照
   - モックデータと実APIの両方をサポート

#### Google Chat API

同様に `services/google_chat.py` を参照してください。

### Vertex AI統合の方法

1. **Vertex AI APIの有効化**
   - Google Cloud ConsoleでVertex AI APIを有効化
   - サービスアカウントに `roles/aiplatform.user` ロールを付与

2. **LLMサービスの使用**
   - `services/llm_service.py` を使用
   - `LLMService.analyze_structure()` で構造的問題検知
   - `LLMService.generate_tasks()` でタスク生成

詳細は [Vertex AI設定ガイド](./backend/VERTEX_AI_SETUP.md) を参照してください。

### モックデータの使用方法

現在、すべてのサービスはモックデータをサポートしています。

- 認証情報が設定されていない場合、自動的にモックモードになります
- モックデータは `services/` ディレクトリ内の各サービスファイルに定義されています

---

## テスト

### ユニットテスト

```bash
cd Dev/backend
pytest tests/unit/
```

### 統合テスト

```bash
pytest tests/integration/
```

### E2Eテスト

```bash
pytest tests/e2e/
```

---

## デバッグ

### よくある問題

1. **ポート競合**
   - ポート8000が使用中の場合は、別のポートを指定
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8001
   ```

2. **CORSエラー**
   - `config.py` のCORS設定を確認

3. **モックデータが表示されない**
   - 認証情報が設定されている場合、実APIモードになります
   - モックモードにするには、認証情報を削除

### ログの確認

- バックエンドのログは標準出力に出力されます
- リクエストIDで特定のリクエストを追跡できます

---

## 参考資料

- [APIドキュメント](./backend/API_DOCUMENTATION.md)
- [アーキテクチャドキュメント](./ARCHITECTURE.md)
- [クイックスタートガイド](./QUICKSTART.md)
- [バックエンドセットアップガイド](./backend/SETUP.md)
