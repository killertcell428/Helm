# ステップ4: Google Meet API実装 - ユーザー作業ガイド

## 📋 作業内容

Google Meet APIを使用するための準備作業です。以下の手順に従って進めてください。

## ✅ チェックリスト

### 1. Google Meet APIの有効化

- [×] [Google Cloud Console](https://console.cloud.google.com/) にアクセス
- [×] プロジェクト `helm-project-484105` を選択
- [×] 左メニューから「APIとサービス」>「ライブラリ」を選択
- [×] 検索ボックスに「Google Meet API」と入力
- [×] 「Google Meet API」を選択
- [×] 「有効にする」ボタンをクリック
- [×] 有効化が完了するまで待つ（数秒〜1分）

### 2. OAuth認証のスコープ追加（既にOAuth認証を設定済みの場合）

ステップ1でOAuth認証を設定済みの場合は、Google Meet APIのスコープを追加する必要があります。

**手順**:
- [×] 「APIとサービス」>「OAuth同意画面」を選択
- [×] 「スコープを追加または削除」をクリック
- [×] `https://www.googleapis.com/auth/meetings.space.readonly` を追加（読み取り専用）
  -または `https://www.googleapis.com/auth/meetings.space` を追加（読み書き）
- [×] 「更新」>「保存して次へ」をクリック

**重要**: スコープを追加した後、再度認証が必要な場合があります。
- 既存のトークンファイル（`credentials/token.json`）を削除
- `python setup_oauth_token.py` を実行して再認証

### 3. 動作確認

以下のコマンドで環境変数が正しく設定されているか確認：

```powershell
# OAuth認証情報ファイルの確認
echo $env:GOOGLE_OAUTH_CREDENTIALS_FILE

# フォルダIDの確認（Google Driveで作成したフォルダ）
echo $env:GOOGLE_DRIVE_FOLDER_ID

# プロジェクトIDの確認
echo $env:GOOGLE_CLOUD_PROJECT_ID
```

すべて正しい値が表示されればOKです。

## 📝 メモ欄

作業中にメモしておくと便利な情報：

- **Google Meet API有効化日**: `___________________________`
- **OAuthスコープ追加日**: `___________________________`（必要な場合のみ）

## ⚠️ 注意事項

1. **OAuth認証を使用する場合**
   - ステップ1でOAuth認証を設定済みの場合は、追加の認証設定は不要です
   - Google Meet APIのスコープ（`https://www.googleapis.com/auth/meetings.space.readonly`）が追加されていることを確認してください

2. **サービスアカウントを使用する場合**
   - ステップ1でサービスアカウントを設定済みの場合は、追加の認証設定は不要です
   - Google Meet APIの有効化のみ必要です

3. **Google Meet APIの制限事項**
   - Google Meet APIは、Google Workspaceアカウントが必要な場合があります
   - 個人のGoogleアカウントでは、一部の機能が制限される可能性があります
   - 議事録の取得には、会議の主催者または参加者である必要があります
   - 詳細は [Google Meet API ドキュメント](https://developers.google.com/meet/api) を参照してください

4. **コスト**
   - Google Meet APIは無料枠がありますが、大量使用時はコストが発生する可能性があります
   - [Google Cloud Pricing](https://cloud.google.com/pricing) で確認してください

## ✅ 完了確認

すべてのチェック項目が完了したら、以下を確認してください：

- [ ] Google Meet APIが有効化されている
- [ ] OAuthスコープが追加されている（OAuth認証使用時）
- [ ] 環境変数が正しく設定されている

完了したら、開発者に「ステップ4のユーザー作業が完了しました」と伝えてください。

## 🆘 トラブルシューティング

### APIが有効化されない

- Google Cloud Consoleで、APIの有効化が完了しているか確認
- 数分待ってから再度確認

### OAuthスコープエラー

- OAuth同意画面で、`https://www.googleapis.com/auth/meetings.space.readonly` スコープが追加されているか確認
- スコープを追加した後、再度認証が必要な場合があります（`python setup_oauth_token.py`）

### Google Workspaceアカウントが必要

- 個人のGoogleアカウントでは、Google Meet APIが制限される可能性があります
- その場合は、モックモードで動作します

### 議事録が取得できない

- 会議の主催者または参加者である必要があります
- 会議が終了している必要があります
- 議事録が有効になっている必要があります

---

**次のステップ**: ユーザー作業が完了したら、開発者がコーディング実装を開始します。
