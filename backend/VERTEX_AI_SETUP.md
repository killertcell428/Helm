# Vertex AI / Gemini統合セットアップガイド

## 概要

Helmでは、構造的問題検知と説明文生成にVertex AI / Geminiを使用します。
環境変数が設定されていない場合は、自動的にモックモードにフォールバックします。

## セットアップ方法

### 1. Google Cloud Projectの準備

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成（または既存のプロジェクトを使用）
3. Vertex AI APIを有効化

### 2. 認証情報の設定

#### 方法1: サービスアカウント（推奨・本番環境）

```bash
# サービスアカウントキーをダウンロード
gcloud iam service-accounts create helm-service-account
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:helm-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud iam service-accounts keys create credentials.json \
  --iam-account=helm-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com

# 環境変数を設定
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
export GOOGLE_CLOUD_PROJECT_ID="YOUR_PROJECT_ID"
```

#### 方法2: gcloud認証（開発環境）

```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT_ID="YOUR_PROJECT_ID"
```

### 3. 依存関係のインストール

```bash
cd Dev/backend
pip install -r requirements.txt
```

`requirements.txt` には以下が含まれています：
- `google-cloud-aiplatform>=1.38.1`

### 4. 環境変数の設定

`.env` ファイルを作成（または環境変数を設定）：

```bash
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json  # サービスアカウント使用時
```

### 5. 動作確認

バックエンドサーバーを起動：

```bash
uvicorn main:app --reload
```

環境変数が設定されている場合、Vertex AIが使用されます。
設定されていない場合、自動的にモックモードにフォールバックします。

## モックモードと実APIモードの切り替え

### モックモード（デフォルト）

環境変数が設定されていない場合、自動的にモックモードになります。
- 実際のAPI呼び出しは行われません
- ルールベースの分析結果を返します
- 開発・テストに最適

### 実APIモード

環境変数を設定すると、実際のVertex AI / Gemini APIが使用されます：
- より高度な分析が可能
- 説明文がより詳細に生成される
- APIコストが発生します

## エラーハンドリング

- Vertex AI APIでエラーが発生した場合、自動的にモックモードにフォールバック
- エラーログがコンソールに出力されます
- アプリケーションは継続して動作します

## トラブルシューティング

### エラー: `google-cloud-aiplatformがインストールされていません`

```bash
pip install google-cloud-aiplatform
```

### エラー: `GOOGLE_CLOUD_PROJECT_ID環境変数が設定されていません`

環境変数を設定するか、モックモードを使用してください。

### エラー: 認証エラー

```bash
# 認証情報を確認
gcloud auth list

# 再認証
gcloud auth application-default login
```

## コスト

Vertex AI / Gemini APIの使用にはコストが発生します。
詳細は [Vertex AI 料金](https://cloud.google.com/vertex-ai/pricing) を参照してください。

開発・テスト時はモックモードを使用することを推奨します。

