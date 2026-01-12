# 個人のGoogle Driveを使用する方法（Google Workspace不要）

## 概要

Google Workspaceアカウントがなくても、個人のGoogleアカウントでGoogle Drive APIを使用できます。

## 方法1: OAuth認証で個人のGoogle Driveフォルダを使用（推奨）

### 前提条件

- 個人のGoogleアカウント
- Google Cloud Project（既に作成済み）

### セットアップ手順

#### 1. OAuth同意画面の設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 「APIとサービス」>「OAuth同意画面」を選択
3. ユーザータイプを選択：
   - **外部** を選択（個人アカウントで使用する場合）
   - 「作成」をクリック
4. アプリ情報を入力：
   - **アプリ名**: `Helm Project`
   - **ユーザーサポートメール**: あなたのメールアドレス
   - **デベロッパーの連絡先情報**: あなたのメールアドレス
5. 「保存して次へ」をクリック
6. スコープの追加：
   - 「スコープを追加または削除」をクリック
   - 以下のスコープを追加：
     - `https://www.googleapis.com/auth/drive.file`（ファイルの作成・編集）
     - `https://www.googleapis.com/auth/drive.readonly`（読み取り専用）
   - 「更新」>「保存して次へ」をクリック
7. テストユーザーの追加：
   - 「ユーザーを追加」をクリック
   - あなたのGoogleアカウントのメールアドレスを追加
   - 「保存して次へ」をクリック
8. 「ダッシュボードに戻る」をクリック

#### 2. OAuth 2.0 クライアントIDの作成

1. 「APIとサービス」>「認証情報」を選択
2. 「認証情報を作成」>「OAuth 2.0 クライアントID」をクリック
3. アプリケーションの種類: **デスクトップアプリ** を選択
4. 名前: `Helm Desktop Client` を入力
5. 「作成」をクリック
6. **クライアントID** と **クライアントシークレット** をメモ（後で使用します）
7. 「OK」をクリック

#### 3. 認証情報ファイルのダウンロード

1. 作成したOAuth 2.0 クライアントIDをクリック
2. 「JSONをダウンロード」をクリック
3. ダウンロードしたJSONファイルを保存
   - 推奨パス: `C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend\credentials\oauth_credentials.json`
   - ファイル名は任意（例: `oauth_client_secret.json`）

#### 4. Google Driveフォルダの事前作成

1. [Google Drive](https://drive.google.com/) にアクセス
2. 新しいフォルダを作成（例: `Helm Project Files`）
3. フォルダを開く
4. URLからフォルダIDを取得
   - URL例: `https://drive.google.com/drive/folders/1ABC123xyz...`
   - `folders/` の後の文字列がフォルダID
   - 例: `1ABC123xyz...`

#### 5. 環境変数の設定

`.env` ファイルに以下を追加：

```env
# OAuth認証情報
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_CREDENTIALS_FILE=C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend\credentials\oauth_credentials.json

# Google DriveフォルダID（事前に作成したフォルダ）
GOOGLE_DRIVE_FOLDER_ID=1ABC123xyz...

# プロジェクトID
GOOGLE_CLOUD_PROJECT_ID=helm-project-484105
```

#### 6. 初回認証（トークンの取得）

初回のみ、ブラウザで認証を行い、トークンを取得する必要があります。

```bash
python setup_oauth_token.py
```

このスクリプトを実行すると、ブラウザが開き、Googleアカウントでログインして認証を行います。

---

## 方法2: ローカルファイルシステムに保存（開発用）

Google Driveを使わず、ローカルにファイルを保存する方法です。

### 実装方法

環境変数で保存先を切り替え：

```env
# ローカル保存モード
FILE_STORAGE_MODE=local
FILE_STORAGE_PATH=C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend\storage
```

この方法では、ファイルはローカルに保存され、必要に応じて手動でGoogle Driveにアップロードできます。

---

## 方法3: サービスアカウント + 個人フォルダの共有（制限あり）

サービスアカウントを個人のGoogle Driveフォルダに共有する方法ですが、**サービスアカウントにはストレージクォータがないため、この方法は動作しません**。

---

## 推奨方法

**方法1（OAuth認証）** を推奨します。理由：
- 個人のGoogleアカウントで使用可能
- Google Driveの機能をフル活用できる
- フォルダを事前に作成して管理しやすい

---

## 実装の切り替え

開発者がOAuth認証に対応した実装を追加します。これにより：
- サービスアカウントモード（共有ドライブ必要）
- OAuth認証モード（個人フォルダ使用可能）
- ローカル保存モード（開発用）

の3つのモードから選択できるようになります。
