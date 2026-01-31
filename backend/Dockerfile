FROM python:3.11-slim

WORKDIR /app

# システムパッケージの更新とクリーンアップ
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 依存関係のインストール（キャッシュ最適化のため先にコピー）
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# 非rootユーザーの作成（セキュリティ）
# ログディレクトリと出力ディレクトリを作成（非rootユーザーが書き込めるように）
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs /tmp/outputs && \
    chown -R appuser:appuser /app /tmp/outputs
USER appuser

# ポート公開（Cloud RunはデフォルトでPORT=8080を提供）
EXPOSE 8080

# Cloud RunはPORT環境変数を自動的に設定するため、ENV PORTは不要
# アプリケーション起動（環境変数PORTを使用、デフォルトは8080）
# PythonスクリプトでPORT環境変数を読み取る
CMD python -c "import os; port = int(os.environ.get('PORT', 8080)); import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=port)"

