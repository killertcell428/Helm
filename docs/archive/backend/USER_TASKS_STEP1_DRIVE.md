# ステップ1: Google Drive API実装 - ユーザー作業ガイド

## 📋 作業内容

Google Drive APIを使用するための準備作業です。以下の手順に従って進めてください。

## ✅ チェックリスト

### 1. Google Cloud Projectの作成

- [×] [Google Cloud Console](https://console.cloud.google.com/) にアクセス
- [×] 新しいプロジェクトを作成（または既存のプロジェクトを使用）
  - プロジェクト名: `Helm Project`（任意）
  - プロジェクトID: `helm-project-xxxxx`（自動生成、メモしておく）
- [×] プロジェクトIDをメモ: `helm-project-484105`

### 2. Google Drive APIの有効化

- [×] 左メニューから「APIとサービス」>「ライブラリ」を選択
- [×] 検索ボックスに「Google Drive API」と入力
- [×] 「Google Drive API」を選択
- [×] 「有効にする」ボタンをクリック
- [×] 有効化が完了するまで待つ（数秒〜1分）

### 3. サービスアカウントの作成

- [×] 左メニューから「IAMと管理」>「サービスアカウント」を選択
- [×] 「サービスアカウントを作成」ボタンをクリック
- [ ] サービスアカウントの詳細を入力：
  - **サービスアカウント名**: `helm-drive-service`
  - **サービスアカウントID**: `helm-drive-service`（自動入力）
  - **説明**: `Helm Google Drive API用サービスアカウント`
- [×] 「作成して続行」をクリック

### 4. 権限の付与

- [×] 「このサービスアカウントにロールを付与」セクションで：
  - 「ロールを選択」ドロップダウンをクリック
  - 「Google Drive API」を検索
  - 「ドライブ API ユーザー」を選択
- [×] 「続行」をクリック
- [×] 「完了」をクリック

### 5. 認証情報（JSON）のダウンロード

- [×] 作成したサービスアカウント（`helm-drive-service@...`）をクリック
- [×] 「キー」タブを選択
- [×] 「キーを追加」>「新しいキーを作成」をクリック
- [×] キーのタイプ: **JSON** を選択
- [×] 「作成」をクリック
- [×] JSONファイルが自動的にダウンロードされる
- [×] ダウンロードされたファイル名を確認（ `helm-project-484105-e452e434565d.json`）
- [×] ファイルを安全な場所に保存
  - パス: `C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend\credentials\`
  - **重要**: このファイルは秘密情報です。Gitにコミットしないでください

### 6. 環境変数の設定

以下のいずれかの方法で環境変数を設定してください。

#### 方法A: PowerShellで一時的に設定（現在のセッションのみ）

```powershell
# 認証情報ファイルのパスを設定（実際のパスに置き換えてください）
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend\credentials\helm-project-484105-e452e434565d.json"

# プロジェクトIDを設定（実際のプロジェクトIDに置き換えてください）
$env:GOOGLE_CLOUD_PROJECT_ID="helm-project-484105"
```

#### 方法B: .envファイルに追加（推奨）

1. `Dev/backend/.env` ファイルを作成（存在しない場合）
2. 以下の内容を追加：

```env
GOOGLE_APPLICATION_CREDENTIALS=C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend\credentials\helm-project-484105-e452e434565d.json
GOOGLE_CLOUD_PROJECT_ID=helm-project-484105
```

**注意**: `.env` ファイルは `.gitignore` に追加されていることを確認してください。

### 7. 動作確認

以下のコマンドで環境変数が正しく設定されているか確認：

```powershell
# 認証情報ファイルのパスを確認
echo $env:GOOGLE_APPLICATION_CREDENTIALS

# プロジェクトIDを確認
echo $env:GOOGLE_CLOUD_PROJECT_ID

# ファイルが存在するか確認
Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS
```

すべて `True` または正しい値が表示されればOKです。

## 📝 メモ欄

作業中にメモしておくと便利な情報：

- **プロジェクトID**: `___________________________`
- **サービスアカウント名**: `helm-drive-service@___________________________`
- **認証情報ファイルのパス**: `___________________________`
- **作業完了日**: `___________________________`

## ⚠️ 注意事項

1. **認証情報ファイルの管理**
   - JSONファイルは秘密情報です
   - Gitにコミットしないでください
   - 共有しないでください
   - 定期的にローテーションすることを推奨

2. **コスト**
   - Google Drive APIは無料枠がありますが、大量使用時はコストが発生する可能性があります
   - [Google Cloud Pricing](https://cloud.google.com/pricing) で確認してください

3. **権限**
   - サービスアカウントには必要最小限の権限のみを付与してください
   - 本番環境では、より厳格な権限管理を推奨します

## ✅ 完了確認

すべてのチェック項目が完了したら、以下を確認してください：

- [ ] 環境変数が正しく設定されている
- [ ] 認証情報ファイルが存在する
- [ ] プロジェクトIDが正しく設定されている

完了したら、開発者に「ステップ1のユーザー作業が完了しました」と伝えてください。

## ⚠️ 重要: 共有ドライブ（Shared Drive）の設定が必要です

サービスアカウントにはストレージクォータがないため、**共有ドライブ（Shared Drive）**の設定が必要です。

詳細は [SETUP_SHARED_DRIVE.md](./SETUP_SHARED_DRIVE.md) を参照してください。

### クイックセットアップ

1. Google Workspaceアカウントで [Google Drive](https://drive.google.com/) にアクセス
2. 左メニューから「共有ドライブ」を選択して新規作成
3. サービスアカウント（`helm-drive-service@helm-project-484105.iam.gserviceaccount.com`）をメンバーに追加（権限: コンテンツ管理者）
4. 共有ドライブのURLからIDを取得（`folders/` の後の文字列）
5. `.env` ファイルに追加：
   ```env
   GOOGLE_DRIVE_SHARED_DRIVE_ID=共有ドライブID
   ```

## 🆘 トラブルシューティング

### 認証情報ファイルが見つからない

- ファイルのパスが正しいか確認
- ファイル名にスペースや特殊文字が含まれていないか確認
- 絶対パスを使用しているか確認

### 環境変数が設定されない

- PowerShellを再起動してみる
- `.env` ファイルを使用する場合は、アプリケーションが `.env` ファイルを読み込む設定になっているか確認

### APIが有効化されない

- Google Cloud Consoleで、APIの有効化が完了しているか確認
- 数分待ってから再度確認

---
　
**次のステップ**: ユーザー作業が完了したら、開発者がコーディング実装を開始します。
