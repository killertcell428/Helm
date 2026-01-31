# 課金アカウントの設定ガイド

## ⚠️ 現在の状況

プロジェクト `reacha-app-20251224141452` は作成されましたが、**課金アカウントが設定されていない**ため、Cloud Runなどのサービスを使用できません。

## 💳 課金アカウントの設定方法

### 方法1: Google Cloud Consoleから設定（推奨）

1. **Google Cloud Consoleにアクセス**
   - https://console.cloud.google.com/billing にアクセス
   - または、プロジェクトページから「課金」を選択

2. **課金アカウントをリンク**
   - 「課金アカウントをリンク」をクリック
   - 既存の課金アカウントを選択、または新しい課金アカウントを作成
   - プロジェクト `reacha-app-20251224141452` を選択してリンク

3. **確認**
   - プロジェクトページで「課金が有効」と表示されることを確認

### 方法2: コマンドラインから設定

既存の課金アカウントがある場合：

```powershell
# 課金アカウントの一覧を確認
gcloud billing accounts list

# 課金アカウントIDを取得（例: 012345-67890A-BCDEFG）
# プロジェクトにリンク
gcloud billing projects link reacha-app-20251224141452 --billing-account=BILLING_ACCOUNT_ID
```

## ✅ 課金アカウント設定後の手順

課金アカウントを設定したら、以下のコマンドでAPIを有効化：

```powershell
# プロジェクトを確認
gcloud config get-value project

# 必要なAPIを有効化
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

または、セットアップスクリプトを再実行：

```powershell
.\gcloud\scripts\setup_project.ps1
```

## 💰 料金について

Google Cloud Runは従量課金制です：
- **無料枠**: 毎月200万リクエスト、360,000 GiB秒、180,000 vCPU秒
- **超過分**: リクエスト数、CPU時間、メモリ使用量に応じて課金

詳細: https://cloud.google.com/run/pricing

## 📝 次のステップ

課金アカウントを設定してAPIを有効化したら：

1. **フロントエンドをビルド**
   ```powershell
   cd flont
   npm run build
   cd ..
   ```

2. **デプロイ**
   ```powershell
   .\deploy.ps1
   ```

## 🔗 参考リンク

- [Google Cloud 課金アカウントの設定](https://cloud.google.com/billing/docs/how-to/manage-billing-account)
- [Cloud Run 料金](https://cloud.google.com/run/pricing)
- [無料トライアル](https://cloud.google.com/free)

---

**課金アカウントを設定したら、APIを有効化してデプロイを進めてください！**
