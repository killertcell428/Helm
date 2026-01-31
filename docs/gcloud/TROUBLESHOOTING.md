# トラブルシューティングガイド

Helm Backend APIのデプロイ時に発生する可能性のある問題と解決方法をまとめています。

## 目次

1. [デプロイ前の問題](#デプロイ前の問題)
2. [デプロイ中の問題](#デプロイ中の問題)
3. [デプロイ後の問題](#デプロイ後の問題)
4. [環境変数関連の問題](#環境変数関連の問題)
5. [認証関連の問題](#認証関連の問題)

---

## デプロイ前の問題

### 問題1: `gcloud` コマンドが見つからない

**症状**:
```
gcloud : 用語 'gcloud' は、コマンドレット、関数、スクリプト ファイル、または操作可能なプログラムの名前として認識されません。
```

**解決方法**:

1. **新しいPowerShellを開く**
   - PATHが更新されるため、新しいセッションを開いてください

2. **PATHを手動で更新**:
   ```powershell
   $env:Path += ";C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin"
   ```

3. **環境変数に永続的に追加**:
   - Windowsキー + R → `sysdm.cpl` → Enter
   - 「詳細設定」→「環境変数」
   - 「システム環境変数」の「Path」を編集
   - `C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin` を追加

4. **Google Cloud SDKを再インストール**:
   - https://cloud.google.com/sdk/docs/install から再インストール

### 問題2: Pythonが見つからない

**症状**:
```
To use the Google Cloud CLI, you must have Python installed and on your PATH.
```

**解決方法**:

1. **Pythonがインストールされているか確認**:
   ```powershell
   python --version
   where python
   ```

2. **環境変数 `CLOUDSDK_PYTHON` を設定**:
   ```powershell
   $pythonPath = (Get-Command python).Source
   $env:CLOUDSDK_PYTHON = $pythonPath
   [System.Environment]::SetEnvironmentVariable("CLOUDSDK_PYTHON", $pythonPath, "User")
   ```

3. **新しいPowerShellを開いて確認**:
   ```powershell
   gcloud version
   ```

### 問題3: Dockerが見つからない、または起動していない

**症状**:
```
docker: command not found
または
Cannot connect to the Docker daemon
```

**解決方法**:

1. **Docker Desktopが起動しているか確認**:
   - システムトレイにDockerアイコンが表示されているか確認
   - Docker Desktopを起動

2. **Dockerのバージョンを確認**:
   ```powershell
   docker version
   ```

3. **Docker Desktopを再起動**:
   - Docker Desktopを終了して再起動

4. **WSL 2が有効になっているか確認**（Windowsの場合）:
   ```powershell
   wsl --list --verbose
   ```

### 問題4: プロジェクトが選択されていない

**症状**:
```
ERROR: (gcloud) Project [None] not found
```

**解決方法**:

```powershell
# プロジェクトを設定
gcloud config set project helm-project-484105

# 確認
gcloud config get-value project
```

---

## デプロイ中の問題

### 問題5: Docker認証エラー

**症状**:
```
error from registry: Unauthenticated request.
denied: Permission denied
```

**解決方法**:

```powershell
# Docker認証を設定
gcloud auth configure-docker gcr.io --quiet

# 認証を確認
gcloud auth list
```

### 問題6: 課金アカウントが設定されていない

**症状**:
```
ERROR: (gcloud.services.enable) FAILED_PRECONDITION: Billing account for project 'helm-project-484105' is not found.
```

**解決方法**:

1. **課金アカウントを確認**:
   ```powershell
   gcloud billing accounts list
   ```

2. **プロジェクトにリンク**:
   ```powershell
   gcloud billing projects link helm-project-484105 --billing-account=BILLING_ACCOUNT_ID
   ```

3. **Google Cloud Consoleから設定**:
   - https://console.cloud.google.com/billing にアクセス
   - 「課金アカウントをリンク」をクリック
   - プロジェクト `helm-project-484105` を選択してリンク

### 問題7: 必要なAPIが有効化されていない

**症状**:
```
ERROR: (gcloud.services.enable) FAILED_PRECONDITION: API [run.googleapis.com] not enabled
```

**解決方法**:

```powershell
# 必要なAPIを有効化
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# 確認
gcloud services list --enabled --project=helm-project-484105
```

### 問題8: Dockerイメージのビルドエラー

**症状**:
```
ERROR: failed to solve: process "/bin/sh -c pip install..." did not complete successfully
```

**解決方法**:

1. **requirements.txtを確認**:
   ```powershell
   cat Dev/backend/requirements.txt
   ```

2. **ローカルでビルドをテスト**:
   ```powershell
   cd Dev/backend
   docker build -t helm-api-test .
   ```

3. **Dockerfileを確認**:
   - 依存関係のインストール順序を確認
   - キャッシュの問題の場合は、`--no-cache` オプションを使用:
     ```powershell
     docker build --no-cache -t helm-api-test .
     ```

### 問題9: イメージのプッシュエラー

**症状**:
```
denied: Permission denied
unauthorized: authentication required
```

**解決方法**:

1. **認証を再設定**:
   ```powershell
   gcloud auth login
   gcloud auth configure-docker gcr.io --quiet
   ```

2. **サービスアカウントを使用している場合**:
   ```powershell
   gcloud auth activate-service-account --key-file=path/to/service-account-key.json
   ```

---

## デプロイ後の問題

### 問題10: サービスが起動しない

**症状**:
- Cloud Runのサービスが「エラー」状態
- ログにエラーメッセージが表示される

**解決方法**:

1. **ログを確認**:
   ```powershell
   gcloud run services logs read helm-api --region asia-northeast1 --limit 100
   ```

2. **環境変数を確認**:
   ```powershell
   gcloud run services describe helm-api --region asia-northeast1 --format="yaml(spec.template.spec.containers[0].env)"
   ```

3. **ローカルでDockerイメージをテスト**:
   ```powershell
   docker run -p 8000:8000 -e GOOGLE_API_KEY=test gcr.io/helm-project-484105/helm-api:latest
   ```

### 問題11: 環境変数が正しく設定されていない

**症状**:
- アプリケーションが環境変数を読み込めない
- ログに「環境変数が設定されていません」というエラー

**解決方法**:

1. **環境変数を確認**:
   ```powershell
   gcloud run services describe helm-api `
     --region asia-northeast1 `
     --format="get(spec.template.spec.containers[0].env)"
   ```

2. **環境変数を再設定**:
   ```powershell
   gcloud run services update helm-api `
     --region asia-northeast1 `
     --update-env-vars "GOOGLE_API_KEY=your-key,USE_LLM=true"
   ```

3. **環境変数の形式を確認**:
   - カンマで区切られているか
   - 引用符が正しく使用されているか
   - スペースがないか

### 問題12: CORSエラー

**症状**:
```
Access to fetch at 'https://helm-api-xxxxx.run.app/api/...' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**解決方法**:

1. **CORS設定を確認**:
   ```powershell
   gcloud run services describe helm-api `
     --region asia-northeast1 `
     --format="get(spec.template.spec.containers[0].env)" | Select-String "CORS"
   ```

2. **CORS_ORIGINS環境変数を設定**:
   ```powershell
   gcloud run services update helm-api `
     --region asia-northeast1 `
     --update-env-vars "CORS_ORIGINS=http://localhost:3000,https://*.vercel.app"
   ```

3. **バックエンドのCORS設定を確認**:
   - `Dev/backend/config.py` の `CORS_ORIGINS` 設定を確認

### 問題13: タイムアウトエラー

**症状**:
```
Request timeout
または
The request exceeded the maximum allowed execution time
```

**解決方法**:

1. **タイムアウト設定を確認**:
   ```powershell
   gcloud run services describe helm-api `
     --region asia-northeast1 `
     --format="get(spec.template.spec.timeoutSeconds)"
   ```

2. **タイムアウトを延長**（最大3600秒）:
   ```powershell
   gcloud run services update helm-api `
     --region asia-northeast1 `
     --timeout 3600
   ```

3. **リソースを増やす**:
   ```powershell
   gcloud run services update helm-api `
     --region asia-northeast1 `
     --memory 4Gi `
     --cpu 4
   ```

### 問題14: メモリ不足エラー

**症状**:
```
Container killed due to memory limit
```

**解決方法**:

```powershell
# メモリを増やす
gcloud run services update helm-api `
  --region asia-northeast1 `
  --memory 4Gi
```

---

## 環境変数関連の問題

### 問題15: 環境変数が更新されない

**症状**:
- 環境変数を更新したが、変更が反映されない

**解決方法**:

1. **新しいリビジョンがデプロイされているか確認**:
   ```powershell
   gcloud run services describe helm-api --region asia-northeast1
   ```

2. **環境変数を再設定**:
   ```powershell
   gcloud run services update helm-api `
     --region asia-northeast1 `
     --update-env-vars "KEY=value"
   ```

3. **サービスを再デプロイ**:
   ```powershell
   cd Dev/backend
   .\deploy.ps1
   ```

### 問題16: 環境変数の値に特殊文字が含まれている

**症状**:
- 環境変数の値にスペースや特殊文字が含まれている場合、正しく設定されない

**解決方法**:

1. **引用符で囲む**:
   ```powershell
   gcloud run services update helm-api `
     --region asia-northeast1 `
     --update-env-vars "KEY='value with spaces'"
   ```

2. **Base64エンコードを使用**（複雑な値の場合）

---

## 認証関連の問題

### 問題17: OAuth認証が失敗する

**症状**:
```
OAuth error: invalid_client
または
OAuth error: redirect_uri_mismatch
```

**解決方法**:

1. **OAuth認証情報を確認**:
   - [認証情報](https://console.cloud.google.com/apis/credentials) でOAuth 2.0 クライアントIDを確認
   - リダイレクトURIが正しく設定されているか確認

2. **リダイレクトURIを追加**:
   - Cloud RunのサービスURLをリダイレクトURIに追加
   - 例: `https://helm-api-xxxxx.asia-northeast1.run.app`

3. **OAuth認証情報ファイルを確認**:
   - JSONファイルが正しくダウンロードされているか
   - ファイルパスが正しいか

### 問題18: APIキーが無効

**症状**:
```
API key not valid
または
Invalid API key
```

**解決方法**:

1. **APIキーを確認**:
   - [Google AI Studio](https://makersuite.google.com/app/apikey) でAPIキーを確認
   - APIキーが有効であることを確認

2. **新しいAPIキーを生成**:
   - 古いAPIキーを無効化
   - 新しいAPIキーを生成
   - 環境変数を更新

3. **APIキーの制限を確認**:
   - APIキーに適切な制限が設定されているか確認

---

## その他の問題

### 問題19: ログが表示されない

**解決方法**:

1. **ログの取得方法を確認**:
   ```powershell
   gcloud run services logs read helm-api --region asia-northeast1 --limit 50
   ```

2. **リアルタイムログを確認**:
   ```powershell
   gcloud run services logs tail helm-api --region asia-northeast1
   ```

3. **Cloud Loggingで確認**:
   - [Cloud Logging](https://console.cloud.google.com/logs) でログを確認

### 問題20: サービスのURLが取得できない

**解決方法**:

```powershell
# サービスのURLを取得
gcloud run services describe helm-api `
  --region asia-northeast1 `
  --format="value(status.url)"
```

---

## サポート

問題が解決しない場合:

1. **ログを確認**:
   ```powershell
   gcloud run services logs read helm-api --region asia-northeast1 --limit 100
   ```

2. **サービスの状態を確認**:
   ```powershell
   gcloud run services describe helm-api --region asia-northeast1
   ```

3. **ドキュメントを参照**:
   - [デプロイ前チェックリスト](./DEPLOY_CHECKLIST.md)
   - [デプロイ後確認手順](./POST_DEPLOY_CHECK.md)
   - [手作業セットアップガイド](./MANUAL_SETUP_GUIDE.md)

4. **Google Cloudサポートに問い合わせ**:
   - [Google Cloudサポート](https://cloud.google.com/support)
