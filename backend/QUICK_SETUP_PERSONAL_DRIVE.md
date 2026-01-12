# 個人のGoogle Driveを使用する - クイックセットアップ

## 概要

Google Workspaceアカウントがなくても、個人のGoogleアカウントでGoogle Drive APIを使用できます。

## セットアップ手順（約10分）

### 1. OAuth同意画面の設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクト `helm-project-484105` を選択
3. 「APIとサービス」>「OAuth同意画面」を選択
4. **ユーザータイプ**: **外部** を選択 → 「作成」
5. **アプリ情報**を入力：
   - アプリ名: `Helm Project`
   - ユーザーサポートメール: あなたのメールアドレス
   - デベロッパーの連絡先情報: あなたのメールアドレス
6. 「保存して次へ」をクリック
7. **スコープ**:
   - 「スコープを追加または削除」をクリック
   - 以下のスコープを追加：
     - `https://www.googleapis.com/auth/drive.file`（Google Drive API）
     - `https://www.googleapis.com/auth/documents`（Google Docs API）
     - `https://www.googleapis.com/auth/chat.messages.readonly`（Google Chat API、読み取り専用）
     - `https://www.googleapis.com/auth/meetings.space.readonly`（Google Meet API、読み取り専用）
   - 「更新」>「保存して次へ」
8. **テストユーザー**:
   - 「ユーザーを追加」をクリック
   - あなたのGoogleアカウントのメールアドレスを追加
   - 「保存して次へ」
9. 「ダッシュボードに戻る」をクリック

### 2. OAuth 2.0 クライアントIDの作成

1. 「APIとサービス」>「認証情報」を選択
2. 「認証情報を作成」>「OAuth 2.0 クライアントID」をクリック
3. **アプリケーションの種類**: **デスクトップアプリ** を選択
4. **名前**: `Helm Desktop Client` を入力
5. 「作成」をクリック
6. **JSONをダウンロード**をクリック
7. ダウンロードしたJSONファイルを保存
   - 推奨パス: `C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend\credentials\oauth_credentials.json`

### 3. Google Driveフォルダの作成

1. [Google Drive](https://drive.google.com/) にアクセス
2. 「新規」>「フォルダ」をクリック
3. フォルダ名: `Helm Project Files` を入力
4. 「作成」をクリック
5. フォルダを開く
6. URLからフォルダIDを取得
   - URL例: `https://drive.google.com/drive/folders/1ABC123xyz...`
   　　https://drive.google.com/drive/folders/1__oEJ7N5pSqKqzsHxBrn0Yb9Eh1cYQmx
   - `folders/` の後の文字列がフォルダID
   - 例: `1ABC123xyz...`

### 4. 環境変数の設定

`.env` ファイルに以下を追加：

```env
# OAuth認証（個人のGoogleアカウント使用）
GOOGLE_OAUTH_CREDENTIALS_FILE=C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend\credentials\oauth_credentials.json

# Google DriveフォルダID（事前に作成したフォルダ）
GOOGLE_DRIVE_FOLDER_ID=1__oEJ7N5pSqKqzsHxBrn0Yb9Eh1cYQmx

# プロジェクトID
GOOGLE_CLOUD_PROJECT_ID=helm-project-484105
```

**注意**: サービスアカウントの認証情報（`GOOGLE_APPLICATION_CREDENTIALS`）は設定しないでください。OAuth認証を使用する場合は不要です。

### 5. 初回認証（トークンの取得）

初回のみ、ブラウザで認証を行います：

```bash
python setup_oauth_token.py
```

このスクリプトを実行すると：
1. ブラウザが自動的に開きます
2. Googleアカウントでログイン
3. アプリのアクセス許可を確認
4. トークンが自動的に保存されます

### 6. 動作確認

```bash
python test_google_drive_real.py
```

## 認証モードの切り替え

### OAuth認証モード（個人アカウント）

`.env` ファイル:
```env
GOOGLE_OAUTH_CREDENTIALS_FILE=path/to/oauth_credentials.json
GOOGLE_DRIVE_FOLDER_ID=your-folder-id
```

### サービスアカウントモード（共有ドライブ必要）

`.env` ファイル:
```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GOOGLE_DRIVE_SHARED_DRIVE_ID=your-shared-drive-id
```

### モックモード（開発用）

上記の環境変数を設定しない場合、自動的にモックモードになります。

## トラブルシューティング

### 認証エラー

- OAuth認証情報ファイルが正しいパスにあるか確認
- テストユーザーに自分のメールアドレスが追加されているか確認

### フォルダが見つからない

- フォルダIDが正しいか確認
- フォルダが存在するか確認

### トークンの有効期限

- トークンは自動的にリフレッシュされます
- 問題が発生した場合は、`credentials/token.json` を削除して再認証

## 参考

詳細は [SETUP_PERSONAL_DRIVE.md](./SETUP_PERSONAL_DRIVE.md) を参照してください。
