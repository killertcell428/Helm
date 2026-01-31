# Docker セットアップガイド

## 現在の状況

フロントエンドのビルドは成功しましたが、**Dockerがインストールされていない**か、PATHに設定されていません。

## 📥 Docker Desktop のインストール

### 方法1: Docker Desktop をインストール（推奨）

1. **Docker Desktop をダウンロード**
   - https://www.docker.com/products/docker-desktop/ にアクセス
   - 「Download for Windows」をクリック

2. **インストール**
   - ダウンロードした `.exe` ファイルを実行
   - インストール時に「Use WSL 2 instead of Hyper-V」を推奨（Windows 11の場合）

3. **起動と確認**
   - Docker Desktopを起動
   - システムトレイにDockerアイコンが表示されることを確認
   - PowerShellで確認：
     ```powershell
     docker version
     ```

### 方法2: Cloud Build を使用（Docker不要）

Dockerをインストールせずに、Google Cloud Buildを使用してデプロイすることもできます。

```powershell
# Cloud Buildでビルドとデプロイを実行
gcloud builds submit --config cloudbuild.yaml
```

## ✅ Docker インストール後の確認

Docker Desktopをインストールしたら：

1. **Docker Desktopを起動**
   - システムトレイにDockerアイコンが表示されるまで待つ

2. **PATHを更新**
   ```powershell
   .\gcloud\scripts\refresh_path.ps1
   ```

3. **動作確認**
   ```powershell
   docker version
   ```

4. **デプロイを再実行**
   ```powershell
   .\deploy.ps1
   ```

## 🔄 代替方法: Cloud Build を使用

Dockerをインストールしたくない場合、Cloud Buildを使用できます：

```powershell
# フロントエンドをビルド（既に完了）
cd flont
npm run build
cd ..

# Cloud Buildでデプロイ
gcloud builds submit --config cloudbuild.yaml
```

## 📝 注意事項

- Docker Desktopは起動している必要があります
- 初回起動時は数分かかることがあります
- WSL 2が必要な場合があります（Windows 10/11）

## 🔗 参考リンク

- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
- [Docker インストールガイド](https://docs.docker.com/desktop/install/windows-install/)

---

**Docker Desktopをインストールしたら、`.\gcloud\scripts\refresh_path.ps1` を実行してから `.\deploy.ps1` を再実行してください！**
