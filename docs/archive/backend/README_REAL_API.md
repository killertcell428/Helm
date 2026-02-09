# 実API実装 - クイックスタート

## 📋 実装の流れ

実API実装は、**ユーザー作業**と**コーディング実装**を交互に進めます。

## 🚀 ステップ1: Google Drive API実装から開始

### 認証方法の選択

Google Drive APIを使用するには、2つの方法から選択できます：

1. **OAuth認証（個人のGoogleアカウント）** ⭐ 推奨
   - Google Workspaceアカウント不要
   - セットアップ: [QUICK_SETUP_PERSONAL_DRIVE.md](./QUICK_SETUP_PERSONAL_DRIVE.md)
   - 所要時間: 約10分

2. **サービスアカウント（共有ドライブ必要）**
   - Google Workspaceアカウント必要
   - セットアップ: [USER_TASKS_STEP1_DRIVE.md](./USER_TASKS_STEP1_DRIVE.md) + [SETUP_SHARED_DRIVE.md](./SETUP_SHARED_DRIVE.md)
   - 所要時間: 約15-20分

**選択ガイド**: [README_DRIVE_SETUP.md](./README_DRIVE_SETUP.md)

### 1. ユーザー作業（あなたの作業）

#### OAuth認証を使用する場合（推奨）

👉 **[QUICK_SETUP_PERSONAL_DRIVE.md](./QUICK_SETUP_PERSONAL_DRIVE.md)** を開いて作業を開始

**作業内容**:
1. OAuth同意画面の設定
2. OAuth 2.0 クライアントIDの作成
3. Google Driveフォルダの作成
4. 環境変数の設定
5. 初回認証（`python setup_oauth_token.py`）

#### サービスアカウントを使用する場合

👉 **[USER_TASKS_STEP1_DRIVE.md](./USER_TASKS_STEP1_DRIVE.md)** を開いて作業を開始

**作業内容**:
1. Google Cloud Projectの作成
2. Google Drive APIの有効化
3. サービスアカウントの作成
4. 権限の付与
5. 認証情報（JSON）のダウンロード
6. 共有ドライブの作成（[SETUP_SHARED_DRIVE.md](./SETUP_SHARED_DRIVE.md)）
7. 環境変数の設定

### 2. 完了通知

ユーザー作業が完了したら、開発者に「ステップ1のユーザー作業が完了しました」と伝えてください。

### 3. コーディング実装（開発者の作業）

開発者が以下を実装します：
- Google Drive API統合コード
- 認証処理
- エラーハンドリング
- モック/実APIの自動切り替え

### 4. 動作確認

実装完了後、以下を確認：
- 環境変数が設定されている場合、実APIを使用
- 環境変数が設定されていない場合、モックに自動フォールバック

## 📚 関連ドキュメント

- **実装計画**: [REAL_API_IMPLEMENTATION_PLAN.md](./REAL_API_IMPLEMENTATION_PLAN.md)
- **実装状況**: [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md)
- **ステップ1ユーザー作業**: [USER_TASKS_STEP1_DRIVE.md](./USER_TASKS_STEP1_DRIVE.md)

## ⚠️ 重要な注意事項

1. **認証情報ファイルの管理**
   - JSONファイルは秘密情報です
   - Gitにコミットしないでください（`.gitignore`に追加済み）
   - 共有しないでください

2. **環境変数の設定**
   - `.env` ファイルを使用することを推奨
   - `.env` ファイルは `.gitignore` に追加済み

3. **モック/実APIの切り替え**
   - 環境変数が設定されていない場合、自動的にモックモードになります
   - 実API実装後も、モックモードで動作確認が可能です

## 🆘 トラブルシューティング

問題が発生した場合は、各ドキュメントの「トラブルシューティング」セクションを参照してください。

---

**次のステップ**: [USER_TASKS_STEP1_DRIVE.md](./USER_TASKS_STEP1_DRIVE.md) を開いて作業を開始してください。
