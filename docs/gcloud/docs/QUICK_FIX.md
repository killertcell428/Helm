# 🚨 Google Cloud CLI エラー クイック修正

## 問題
```
アクセスが拒否されました。
指定されたファイルが見つかりません。
C:\Program Files (x86)\Google\Cloud SDK\tmpfile
To use the Google Cloud CLI, you must have Python installed and on your PATH.
```

## ⚡ 即座に解決する方法

### 方法1: 自動修正スクリプトを実行（推奨）

1. **PowerShellを管理者として実行**
   - Windowsキー → 「PowerShell」と入力
   - 「Windows PowerShell」を右クリック → 「管理者として実行」

2. **スクリプトを実行**
   ```powershell
   cd C:\Users\uecha\Project_P\work\REACHA
   .\gcloud\scripts\fix_gcloud_setup.ps1
   ```

3. **新しいターミナルを開いて確認**
   ```powershell
   gcloud version
   ```

### 方法2: 手動で環境変数を設定

1. **PowerShellで以下を実行**（現在のセッション用）
   ```powershell
   $env:CLOUDSDK_PYTHON = "C:\Users\uecha\AppData\Local\Programs\Python\Python312\python.exe"
   ```

2. **永続的に設定する場合**
   - Windowsキー + R → `sysdm.cpl` → Enter
   - 「詳細設定」→「環境変数」
   - 「ユーザー環境変数」で「新規」
   - 変数名: `CLOUDSDK_PYTHON`
   - 変数値: `C:\Users\uecha\AppData\Local\Programs\Python\Python312\python.exe`
   - 「OK」をクリック

3. **新しいターミナルを開いて確認**
   ```powershell
   gcloud version
   ```

### 方法3: 一時ディレクトリを作成（管理者権限で）

```powershell
# 管理者権限でPowerShellを開いて実行
New-Item -ItemType Directory -Force -Path "C:\Program Files (x86)\Google\Cloud SDK\tmp"
```

## ✅ 動作確認

環境変数を設定した後、新しいターミナルで：

```powershell
# Google Cloud CLIのバージョン確認
gcloud version

# ログイン（初回のみ）
gcloud auth login
```

## 📝 次のステップ

Google Cloud CLIが正常に動作したら：

1. **プロジェクトを設定**
   ```powershell
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **デプロイを実行**
   ```powershell
   .\deploy.ps1
   ```

## 🔍 詳細情報

より詳しいトラブルシューティングは [`SETUP_GCLOUD_WINDOWS.md`](./SETUP_GCLOUD_WINDOWS.md) を参照してください。

---

**最も簡単な方法**: `.\gcloud\scripts\fix_gcloud_setup.ps1` を管理者権限で実行してください！
