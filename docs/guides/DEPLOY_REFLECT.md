# 変更をデプロイに反映するには

原稿や仕様の内容を**本番環境**（公開URL）に反映する手順です。

## 前提

- **フロントエンド**: https://v0-helm-pdca-demo.vercel.app （Vercel）
- **バックエンド**: https://helm-api-dsy6lzllhq-an.a.run.app （Google Cloud Run）

原稿（`YOUTUBE原稿_v01.md`）やZenn記事は**ドキュメント**なので、そのままでは本番アプリは変わりません。  
「デプロイに反映する」＝**該当するコードを編集したうえで、フロント／バックをそれぞれデプロイする**流れになります。

---

## 1. 何を変えたいかでやることが変わる

| 変えたいもの | 編集する場所 | デプロイ先 |
|--------------|--------------|------------|
| ダッシュボードの文言・指標・タスク一覧 | `Dev/app/v0-helm-demo/`（ページ・コンポーネント） | Vercel（フロント） |
| Case1/2/3 の説明・ボタン文言・デモの流れ | `Dev/app/v0-helm-demo/app/demo/` | Vercel（フロント） |
| APIの挙動・分析ロジック・LLMプロンプト | `Dev/backend/` | Cloud Run（バック） |
| 原稿だけ（動画用の台本） | `Dev/docs/YOUTUBE原稿_v01.md` | **デプロイ不要**（動画収録時に参照するだけ） |

---

## 2. フロントエンドをデプロイに反映する（Vercel）

### 方法A: GitHubに push する（推奨）

Vercel が GitHub と連携している場合、**main ブランチへ push すると自動で本番デプロイ**されます。

```powershell
cd c:\Users\uecha\Project_P\Personal\Google-PJ
git add Dev/app/v0-helm-demo/
git commit -m "ダッシュボード文言更新など"
git push origin main
```

- Vercel ダッシュボードの [Deployments](https://vercel.com/dashboard) でビルド・デプロイ状況を確認できます。
- 失敗した場合はメールまたはダッシュボードで確認し、ビルドログで原因を特定します。

### 方法B: Vercel CLI でデプロイする

Git を使わず、ローカルの変更だけを本番に反映したい場合：

```powershell
cd Dev/app/v0-helm-demo
pnpm install
vercel --prod
```

初回は `vercel login` が必要です。詳細は [Vercel初回デプロイガイド](../gcloud/VERCEL_FIRST_DEPLOY.md) を参照してください。

---

## 3. バックエンドをデプロイに反映する（Cloud Run）

API や分析ロジックを変更した場合のみ実行します。

```powershell
cd Dev/backend
.\deploy.ps1
```

- スクリプトが Docker ビルド → Cloud Run デプロイまで実行します。
- 初回や環境未設定の場合は [Cloud Run クイックスタート](../gcloud/QUICKSTART.md) や [デプロイ前チェックリスト](../gcloud/DEPLOY_CHECKLIST.md) を確認してください。

---

## 4. 原稿の内容をアプリに反映する流れ（例）

1. **原稿で「こう説明する」と決めた**  
   （例: ダッシュボードで「組織の羅針盤」と表示する）
2. **該当する画面のコードを編集**  
   （例: `Dev/app/v0-helm-demo/app/page.tsx` や `components/dashboard/` 内の文言）
3. **ローカルで確認**  
   `cd Dev/app/v0-helm-demo && pnpm dev` で表示を確認
4. **デプロイ**  
   - フロント: 上記「2. フロントエンドをデプロイに反映する」のどちらか  
   - バック: 変更した場合のみ「3. バックエンドをデプロイに反映する」

これで、本番URL（https://v0-helm-pdca-demo.vercel.app）に原稿で決めた内容が反映されます。

---

## 参考リンク

- [Vercel初回デプロイガイド](../gcloud/VERCEL_FIRST_DEPLOY.md)
- [フロントエンド本番デプロイ確認](../gcloud/FRONTEND_DEPLOY_CHECK.md)
- [Cloud Run クイックスタート](../gcloud/QUICKSTART.md)
- [README デプロイ済みサービス](../../README.md#-デプロイ済みサービス)
