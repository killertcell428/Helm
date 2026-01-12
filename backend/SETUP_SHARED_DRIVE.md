# 共有ドライブ（Shared Drive）のセットアップガイド

## 問題

サービスアカウントにはストレージクォータがないため、通常のGoogle Driveにファイルを保存できません。

**エラーメッセージ**:
```
Service Accounts do not have storage quota. Leverage shared drives 
(https://developers.google.com/workspace/drive/api/guides/about-shareddrives), 
or use OAuth delegation instead.
```

## 解決方法

以下の2つの方法があります：

### 方法A: 共有ドライブ（Shared Drive）を使用（Google Workspace必要）

共有ドライブは、Google Workspace組織内で共有されるドライブで、サービスアカウントもファイルを保存できます。

**注意**: Google Workspaceアカウントが必要です。

### 方法B: OAuth認証で個人のGoogle Driveフォルダを使用（推奨・個人アカウント可）

個人のGoogleアカウントでも使用できます。事前にフォルダを作成して、そのフォルダに保存します。

**詳細**: [SETUP_PERSONAL_DRIVE.md](./SETUP_PERSONAL_DRIVE.md) または [QUICK_SETUP_PERSONAL_DRIVE.md](./QUICK_SETUP_PERSONAL_DRIVE.md) を参照してください。

## セットアップ手順

### 前提条件

- Google Workspaceアカウントが必要です（個人のGoogleアカウントでは共有ドライブを作成できません）
- Google Workspace管理者権限、または共有ドライブの作成権限が必要です

### 方法1: Google Workspaceで共有ドライブを作成（推奨）

1. **Google Driveにアクセス**
   - [Google Drive](https://drive.google.com/) にアクセス
   - Google Workspaceアカウントでログイン

2. **共有ドライブを作成**
   - 左メニューから「共有ドライブ」を選択
   - 「新規」ボタンをクリック
   - ドライブ名を入力（例: `Helm Project Files`）
   - 「作成」をクリック

3. **サービスアカウントをメンバーに追加**
   - 作成した共有ドライブを開く
   - 右上の「共有」ボタンをクリック
   - サービスアカウントのメールアドレスを入力
     - 形式: `helm-drive-service@helm-project-484105.iam.gserviceaccount.com`
   - 権限: **コンテンツ管理者** または **編集者** を選択
   - 「送信」をクリック

4. **共有ドライブIDを取得**
   - 共有ドライブのURLを確認
   - URL例: `https://drive.google.com/drive/folders/0ABC123xyz...`
   - `folders/` の後の文字列が共有ドライブIDです
   - 例: `0ABC123xyz...`

5. **環境変数に追加**
   - `.env` ファイルに以下を追加：
   ```env
   GOOGLE_DRIVE_SHARED_DRIVE_ID=0ABC123xyz...
   ```

### 方法2: Google Drive APIで共有ドライブを作成（プログラムから）

以下のPythonスクリプトで共有ドライブを作成できます：

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

credentials = service_account.Credentials.from_service_account_file(
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    scopes=['https://www.googleapis.com/auth/drive']
)

service = build('drive', 'v3', credentials=credentials)

# 共有ドライブを作成
drive_metadata = {
    'name': 'Helm Project Files'
}
drive = service.drives().create(
    requestId='unique-request-id',  # 一意のIDを生成
    body=drive_metadata
).execute()

print(f"共有ドライブID: {drive.get('id')}")
```

**注意**: この方法には特別な権限が必要な場合があります。

### 方法3: 既存の共有ドライブを使用

既に共有ドライブがある場合：

1. 共有ドライブのURLからIDを取得
2. サービスアカウントをメンバーに追加
3. 環境変数に共有ドライブIDを設定

## 環境変数の設定

`.env` ファイルに以下を追加：

```env
GOOGLE_APPLICATION_CREDENTIALS=C:\Users\uecha\Project_P\Personal\Google-PJ\Dev\backend\credentials\helm-project-484105-e452e434565d.json
GOOGLE_CLOUD_PROJECT_ID=helm-project-484105
GOOGLE_DRIVE_SHARED_DRIVE_ID=0ABC123xyz...  # 共有ドライブID
```

## 動作確認

環境変数を設定した後、再度テストを実行：

```bash
python test_google_drive_real.py
```

## トラブルシューティング

### 共有ドライブが見つからない

- サービスアカウントが共有ドライブのメンバーになっているか確認
- 共有ドライブIDが正しいか確認

### 権限エラー

- サービスアカウントに「コンテンツ管理者」または「編集者」権限が付与されているか確認

### Google Workspaceアカウントがない場合

個人のGoogleアカウントでは共有ドライブを作成できません。以下の選択肢があります：

1. **Google Workspaceアカウントを取得**
2. **OAuth委任を使用**（別の実装が必要）
3. **モックモードで開発を続ける**

## 参考リンク

- [共有ドライブについて](https://developers.google.com/workspace/drive/api/guides/about-shareddrives)
- [Google Drive API - 共有ドライブ](https://developers.google.com/drive/api/guides/enable-shareddrives)
