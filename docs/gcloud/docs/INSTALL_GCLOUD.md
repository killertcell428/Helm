# Google Cloud SDK インストールガイド（Windows）

## 現在の状況

✅ **完了**: Python環境変数（`CLOUDSDK_PYTHON`）は設定済み  
❌ **未完了**: Google Cloud SDKがインストールされていません

## 📥 インストール手順

### 方法1: インストーラーを使用（推奨）

1. **Google Cloud SDK インストーラーをダウンロード**
   - https://cloud.google.com/sdk/docs/install にアクセス
   - 「Windows 64-bit」のインストーラーをダウンロード

2. **インストーラーを実行**
   - ダウンロードした `.exe` ファイルを実行
   - **管理者として実行**を推奨
   - インストール時に「Pythonの場所を自動検出」を選択

3. **インストール後の確認**
   - 新しいPowerShellを開く
   - 以下を実行：
     ```powershell
     gcloud version
     ```

### 方法2: スタンドアロン版をインストール

1. **ZIPファイルをダウンロード**
   - https://cloud.google.com/sdk/docs/install から「Windows 64-bit (zip)」をダウンロード

2. **展開**
   - ユーザーディレクトリに展開（例: `C:\Users\uecha\google-cloud-sdk`）

3. **インストールスクリプトを実行**
   ```powershell
   cd C:\Users\uecha\google-cloud-sdk
   .\install.bat
   ```
   - インストール時に「PATHに追加するか？」と聞かれたら「Y」を選択

4. **新しいPowerShellを開いて確認**
   ```powershell
   gcloud version
   ```

## ✅ インストール後の確認

### 1. バージョン確認
```powershell
gcloud version
```

### 2. 初期化
```powershell
gcloud init
```

### 3. ログイン
```powershell
gcloud auth login
```

## 🔧 トラブルシューティング

### エラー: "gcloud is not recognized"

**解決策:**
1. 新しいPowerShellを開く（PATHが更新されるため）
2. それでも解決しない場合、手動でPATHに追加：
   - Windowsキー + R → `sysdm.cpl` → Enter
   - 「詳細設定」→「環境変数」
   - 「システム環境変数」の「Path」を編集
   - `C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin` を追加

### エラー: "Python not found"

**解決策:**
環境変数が正しく設定されているか確認：
```powershell
$env:CLOUDSDK_PYTHON
```

設定されていない場合：
```powershell
$env:CLOUDSDK_PYTHON = "C:\Users\uecha\AppData\Local\Programs\Python\Python312\python.exe"
[System.Environment]::SetEnvironmentVariable("CLOUDSDK_PYTHON", $env:CLOUDSDK_PYTHON, "User")
```

## 📝 次のステップ

Google Cloud SDKのインストールが完了したら：

1. **プロジェクトの設定**
   ```powershell
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **デプロイの実行**
   ```powershell
   .\deploy.ps1
   ```

## 🔗 参考リンク

- [Google Cloud SDK インストールガイド](https://cloud.google.com/sdk/docs/install)
- [Google Cloud SDK トラブルシューティング](https://cloud.google.com/sdk/docs/troubleshooting)

---

**インストールが完了したら、新しいPowerShellを開いて `gcloud version` で確認してください！**
