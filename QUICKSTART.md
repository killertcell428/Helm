# Helm クイックスタートガイド（初心者向け）

このガイドでは、Helmプロジェクトを初めて起動する方法を説明します。

## 前提条件

以下のツールがインストールされている必要があります：

- **Python 3.11以上** - [ダウンロード](https://www.python.org/downloads/)
- **Node.js 18以上** - [ダウンロード](https://nodejs.org/)
- **pnpm** - Node.jsのパッケージマネージャー

### pnpmのインストール

```bash
npm install -g pnpm
```

## ステップ1: バックエンドの起動

### 1-1. バックエンドディレクトリに移動

```bash
cd Dev/backend
```

### 1-2. 仮想環境の作成

**Windowsの場合:**
```bash
python -m venv venv
venv\Scripts\activate
```
仮想環境が有効になると、プロンプトの前に `(venv)` が表示されます。

### 1-3. 依存関係のインストール

**重要:** 初回インストール時は、最小限の依存関係から始めることをおすすめします。

```bash
# 最小限の依存関係（推奨）
pip install -r requirements_minimal.txt
```

または、すべての依存関係をインストールする場合：

```bash
# すべての依存関係（Google Cloudライブラリ含む）
pip install -r requirements.txt
```

**注意:** `requirements.txt` をインストールする場合、Google Cloudライブラリのインストールに時間がかかる場合があります。現在はモックデータを使用しているため、`requirements_minimal.txt` で十分です。

これには数分かかる場合があります。

### 1-4. サーバーの起動

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

成功すると、以下のようなメッセージが表示されます：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 1-5. 動作確認

ブラウザで以下のURLを開いてください：

- **APIドキュメント**: http://localhost:8000/docs
- **ヘルスチェック**: http://localhost:8000

APIドキュメントページが表示されれば成功です。

## ステップ2: フロントエンドの起動

**新しいターミナルウィンドウを開いてください**（バックエンドは起動したままにします）

### 2-1. フロントエンドディレクトリに移動

```bash
cd Dev/app/v0-helm-demo
```

### 2-2. 依存関係のインストール

```bash
pnpm install
```

これには数分かかる場合があります。

### 2-3. 環境変数の設定

`.env.local` ファイルを作成します：

**Windowsの場合:**
```bash
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
```

または、手動で `.env.local` ファイルを作成して、以下の内容を記述してください：

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2-4. 開発サーバーの起動

```bash
pnpm dev
```

成功すると、以下のようなメッセージが表示されます：

```
  ▲ Next.js 16.0.10
  - Local:        http://localhost:3000
  - Ready in 2.3s
```

### 2-5. 動作確認

ブラウザで http://localhost:3000 を開いてください。

Helmのホームページが表示されれば成功です。

## ステップ3: デモの実行

### 3-1. デモページにアクセス

ブラウザで以下のURLを開いてください：

http://localhost:3000/demo/case1

### 3-2. デモの流れ

1. **Before（人だけの場合）** - Helm導入前の状況を確認
2. **Helmがある場合を見る** ボタンをクリック
3. **データ受領直後** - 議事録とチャットが取り込まれる
4. **Helm解析結果を見る** ボタンをクリック
5. **Helm解析完了** - 構造的問題が検知される
6. **Executiveの判断へ** ボタンをクリック
7. **Executiveの判断** - 承認または修正を選択
8. **次アクションを確定** ボタンをクリック
9. **AI実行を開始** ボタンをクリック
10. **AI自律実行中** - タスクが実行される
11. **実行結果受領** - 結果が表示される

## 次のステップ

- [アーキテクチャドキュメント](./ARCHITECTURE.md) を読んで、システムの構造を理解する
- [APIドキュメント](http://localhost:8000/docs) でAPIの詳細を確認する
- [実装状況](./IMPLEMENTATION_STATUS.md) で現在の実装状況を確認する

