# Helm Backend API セットアップガイド

## 前提条件

- Python 3.11以上
- Google Cloud Project（オプション、本番環境用）
- Google API認証情報（オプション、実際のGoogleサービス統合用）

## ローカル開発環境のセットアップ

### 1. 仮想環境の作成

```bash
cd Dev/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 依存関係のインストール

**初回インストール時は、最小限の依存関係から始めることをおすすめします：**

```bash
# 最小限の依存関係（推奨・モックデータ使用時）
pip install -r requirements_minimal.txt
```

または、すべての依存関係をインストールする場合：

```bash
# すべての依存関係（Google Cloudライブラリ含む）
pip install -r requirements.txt
```

**注意:** 
- 現在はモックデータを使用しているため、`requirements_minimal.txt` で十分です
- `requirements.txt` をインストールする場合、Google Cloudライブラリのインストールに時間がかかる場合があります
- Windows環境で `pydantic-core` のインストールエラーが発生する場合は、`requirements_minimal.txt` を使用してください

### 3. 環境変数の設定（オプション）

```bash
cp .env.example .env
# .envファイルを編集して必要な設定を追加
```

現在はモックデータを使用しているため、環境変数の設定は不要です。

### 4. サーバーの起動

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

APIは `http://localhost:8000` で起動します。

APIドキュメントは `http://localhost:8000/docs` で確認できます。

## フロントエンドとの連携

### 1. フロントエンドの起動

```bash
cd Dev/app/v0-helm-demo
pnpm install
pnpm dev
```

### 2. 環境変数の設定

フロントエンドの `.env.local` ファイルに以下を追加：

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Cloud Runへのデプロイ

### 1. Google Cloud Projectの設定

```bash
gcloud config set project YOUR_PROJECT_ID
```

### 2. Cloud Buildでデプロイ

```bash
gcloud builds submit --config cloudbuild.yaml
```

### 3. 手動デプロイ

```bash
# Dockerイメージのビルド
docker build -t gcr.io/YOUR_PROJECT_ID/helm-api .

# Container Registryへのプッシュ
docker push gcr.io/YOUR_PROJECT_ID/helm-api

# Cloud Runへのデプロイ
gcloud run deploy helm-api \
  --image gcr.io/YOUR_PROJECT_ID/helm-api \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated
```

## APIエンドポイント

- `GET /` - ヘルスチェック
- `POST /api/meetings/ingest` - 議事録取り込み
- `POST /api/chat/ingest` - チャット取り込み
- `POST /api/analyze` - 構造的問題検知
- `GET /api/analysis/{id}` - 分析結果取得
- `POST /api/escalate` - Executive呼び出し
- `POST /api/approve` - Executive承認
- `POST /api/execute` - AI自律実行開始
- `GET /api/execution/{id}` - 実行状態取得
- `GET /api/execution/{id}/results` - 実行結果取得

## 現在の実装状況

### 実装済み

- ✅ バックエンドAPI基盤（FastAPI）
- ✅ Google Meet統合（モックデータ）
- ✅ Google Chat統合（モックデータ）
- ✅ 構造的問題検知（ルールベース）
- ✅ Executive呼び出しと承認フロー
- ✅ Google Workspace統合（モックデータ）
- ✅ Google Drive統合（モックデータ）
- ✅ フロントエンドとのAPI連携

### 今後の実装予定

- ⏳ Vertex AI / Gemini統合（実際のAI分析）
- ⏳ 実際のGoogle Meet API統合
- ⏳ 実際のGoogle Chat API統合
- ⏳ 実際のGoogle Workspace API統合
- ⏳ 実際のGoogle Drive API統合
- ⏳ Firestore統合（現在はインメモリストレージ）
- ⏳ バックグラウンドタスク実行

## トラブルシューティング

### CORSエラー

フロントエンドからAPIにアクセスできない場合は、`main.py`のCORS設定を確認してください。

### モックデータの確認

現在はモックデータを使用しているため、実際のGoogleサービスへの接続は不要です。

### ポート競合

ポート8000が使用中の場合は、別のポートを指定してください：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

