# Google Drive API セットアップ - 選択ガイド

## 認証方法の選択

Google Drive APIを使用するには、以下の2つの方法から選択できます：

## 方法1: OAuth認証（個人のGoogleアカウント）⭐ 推奨

**メリット**:
- ✅ 個人のGoogleアカウントで使用可能
- ✅ Google Workspaceアカウント不要
- ✅ 事前にフォルダを作成して管理しやすい

**デメリット**:
- 初回のみブラウザで認証が必要

**セットアップ時間**: 約10分

**セットアップガイド**: [QUICK_SETUP_PERSONAL_DRIVE.md](./QUICK_SETUP_PERSONAL_DRIVE.md)

---

## 方法2: サービスアカウント（共有ドライブ必要）

**メリット**:
- 自動認証（ブラウザ不要）
- サーバー環境に適している

**デメリット**:
- ❌ Google Workspaceアカウントが必要
- ❌ 共有ドライブ（Shared Drive）の作成が必要

**セットアップ時間**: 約15-20分（共有ドライブ作成含む）

**セットアップガイド**: [SETUP_SHARED_DRIVE.md](./SETUP_SHARED_DRIVE.md)

---

## 推奨

**個人開発・テスト環境**: 方法1（OAuth認証）を推奨
- Google Workspaceアカウントが不要
- セットアップが簡単
- 個人のGoogle Driveフォルダを使用

**本番環境・企業環境**: 方法2（サービスアカウント）を推奨
- 自動認証で運用しやすい
- 共有ドライブで管理しやすい

---

## クイックスタート

### OAuth認証を使用する場合

1. [QUICK_SETUP_PERSONAL_DRIVE.md](./QUICK_SETUP_PERSONAL_DRIVE.md) を開く
2. 手順に従ってセットアップ（約10分）
3. 初回認証: `python setup_oauth_token.py`
4. 動作確認: `python test_google_drive_real.py`

### サービスアカウントを使用する場合

1. [SETUP_SHARED_DRIVE.md](./SETUP_SHARED_DRIVE.md) を開く
2. 手順に従ってセットアップ（約15-20分）
3. 動作確認: `python test_google_drive_real.py`

---

## 環境変数の設定例

### OAuth認証モード

```env
GOOGLE_OAUTH_CREDENTIALS_FILE=C:\path\to\oauth_credentials.json
GOOGLE_DRIVE_FOLDER_ID=1ABC123xyz...
GOOGLE_CLOUD_PROJECT_ID=helm-project-484105
```

### サービスアカウントモード

```env
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json
GOOGLE_DRIVE_SHARED_DRIVE_ID=0ABC123xyz...
GOOGLE_CLOUD_PROJECT_ID=helm-project-484105
```

---

## トラブルシューティング

### どちらの方法を使うべきかわからない

- **個人のGoogleアカウントしかない場合**: 方法1（OAuth認証）
- **Google Workspaceアカウントがある場合**: 方法2（サービスアカウント）も選択可能

### 認証エラーが発生する

- 環境変数が正しく設定されているか確認
- 認証情報ファイルが存在するか確認
- トークンファイル（OAuth認証の場合）を削除して再認証
