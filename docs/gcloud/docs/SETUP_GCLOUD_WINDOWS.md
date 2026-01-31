# Google Cloud CLI セットアップガイド（Windows）

このガイドでは、WindowsでGoogle Cloud CLIを正しくセットアップする方法を説明します。

## 🔍 問題の診断

エラーメッセージから、以下の問題が考えられます：
1. PythonがPATHに設定されていない
2. Google Cloud SDKの一時ファイルへのアクセス権限がない
3. Google Cloud SDKのインストールが不完全

## ✅ 解決方法

### 方法1: Pythonの確認と設定（推奨）

#### ステップ1: Pythonがインストールされているか確認

PowerShellまたはコマンドプロンプトで以下を実行：

```powershell
python --version
```

または

```powershell
python3 --version
```

**Pythonがインストールされていない場合：**
1. [Python公式サイト](https://www.python.org/downloads/)からPython 3.11以上をダウンロード
2. インストール時に「Add Python to PATH」にチェックを入れる
3. インストール後、新しいターミナルを開いて再度確認

#### ステップ2: 環境変数の設定

Pythonがインストールされているが、PATHに設定されていない場合：

1. **Pythonの場所を確認**
   ```powershell
   where python
   ```
   または
   ```powershell
   where python3
   ```

2. **環境変数を設定**
   - Windowsキー + R → `sysdm.cpl` と入力 → Enter
   - 「詳細設定」タブ → 「環境変数」をクリック
   - 「システム環境変数」で「新規」をクリック
   - 変数名: `CLOUDSDK_PYTHON`
   - 変数値: Pythonの実行ファイルのパス（例: `C:\Python311\python.exe`）
   - 「OK」をクリック

3. **新しいターミナルを開いて確認**
   ```powershell
   gcloud version
   ```

### 方法2: Google Cloud SDKの再インストール

#### ステップ1: 既存のインストールを削除

1. コントロールパネル → 「プログラムと機能」
2. 「Google Cloud SDK」をアンインストール

#### ステップ2: 最新版をインストール

1. [Google Cloud SDK インストーラー](https://cloud.google.com/sdk/docs/install)からWindows用インストーラーをダウンロード
2. **管理者として実行**でインストーラーを起動
3. インストール時に「Pythonの場所を自動検出」を選択
4. インストール完了後、新しいターミナルを開く

### 方法3: 管理者権限で実行

一時ファイルへのアクセス権限の問題の場合：

1. PowerShellを**管理者として実行**
   - Windowsキー → 「PowerShell」と入力
   - 「Windows PowerShell」を右クリック → 「管理者として実行」

2. 以下のコマンドで権限を確認：
   ```powershell
   icacls "C:\Program Files (x86)\Google\Cloud SDK"
   ```

3. 必要に応じて権限を付与（管理者権限で実行）：
   ```powershell
   icacls "C:\Program Files (x86)\Google\Cloud SDK" /grant Users:F /T
   ```

### 方法4: ユーザーディレクトリにインストール（権限問題の回避）

権限の問題を回避するため、ユーザーディレクトリにインストール：

1. [Google Cloud SDK スタンドアロン版](https://cloud.google.com/sdk/docs/install)をダウンロード
2. ユーザーディレクトリ（例: `C:\Users\YourName\google-cloud-sdk`）に展開
3. インストールスクリプトを実行：
   ```powershell
   cd C:\Users\YourName\google-cloud-sdk
   .\install.bat
   ```
4. インストール時にPATHへの追加を選択

## 🧪 動作確認

セットアップ後、以下で確認：

```powershell
# Google Cloud CLIのバージョン確認
gcloud version

# Pythonの確認
gcloud config list

# ログイン（初回のみ）
gcloud auth login
```

## 🔧 トラブルシューティング

### エラー: "Python not found"

**解決策:**
```powershell
# Pythonのパスを確認
where python

# 環境変数を設定（PowerShellで一時的に）
$env:CLOUDSDK_PYTHON = "C:\Python311\python.exe"

# または永続的に設定
[System.Environment]::SetEnvironmentVariable("CLOUDSDK_PYTHON", "C:\Python311\python.exe", "User")
```

### エラー: "Access Denied"

**解決策:**
1. 管理者権限でPowerShellを実行
2. または、ユーザーディレクトリに再インストール

### エラー: "tmpfile not found"

**解決策:**
```powershell
# 一時ディレクトリを作成（管理者権限で）
New-Item -ItemType Directory -Force -Path "C:\Program Files (x86)\Google\Cloud SDK\tmp"
```

または、環境変数で一時ディレクトリを変更：

```powershell
$env:TMPDIR = "$env:USERPROFILE\AppData\Local\Temp"
```

## 📝 次のステップ

Google Cloud CLIが正常に動作することを確認したら：

1. **プロジェクトの設定**
   ```powershell
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **認証**
   ```powershell
   gcloud auth login
   ```

3. **デプロイの実行**
   ```powershell
   .\deploy.ps1
   ```

## 💡 推奨される解決手順

1. **まず方法1を試す**（Pythonの確認と環境変数設定）
2. それでも解決しない場合は**方法2**（再インストール）
3. 権限の問題が続く場合は**方法4**（ユーザーディレクトリにインストール）

## 📚 参考リンク

- [Google Cloud SDK インストールガイド](https://cloud.google.com/sdk/docs/install)
- [Python ダウンロード](https://www.python.org/downloads/)
- [Google Cloud CLI トラブルシューティング](https://cloud.google.com/sdk/docs/troubleshooting)

---

**問題が解決しない場合は、エラーメッセージの全文を共有してください。**
