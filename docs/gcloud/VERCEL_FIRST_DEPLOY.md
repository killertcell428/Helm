# Vercel初回デプロイガイド

**状況**: "No Production Deployment" が表示されている場合、初回デプロイが必要です。

## 🚀 初回デプロイの方法

### 方法1: Vercel CLIを使用（推奨）

#### ステップ1: Vercel CLIのインストール

```powershell
npm install -g vercel
```

#### ステップ2: Vercelにログイン

```powershell
vercel login
```

ブラウザが開くので、Vercelアカウントでログインします。

#### ステップ3: プロジェクトディレクトリに移動

```powershell
cd Dev/app/v0-helm-demo
```

#### ステップ4: 初回デプロイ

```powershell
vercel --prod
```

初回デプロイ時は、いくつかの質問が表示されます：

1. **Set up and deploy?** → `Y`
2. **Which scope?** → アカウントを選択
3. **Link to existing project?** → `N`（新規プロジェクトの場合）または `Y`（既存プロジェクトにリンク）
4. **Project name?** → `v0-helm-pdca-demo` または任意の名前
5. **Directory?** → `.`（現在のディレクトリ）
6. **Override settings?** → `N`（デフォルト設定を使用）

### 方法2: Vercelダッシュボードからデプロイ

#### ステップ1: GitHubリポジトリを接続

1. [Vercel Dashboard](https://vercel.com/dashboard) にアクセス
2. **Add New...** → **Project** をクリック
3. GitHubリポジトリを選択（またはインポート）
4. リポジトリが表示されない場合は、**Import Git Repository** で追加

#### ステップ2: プロジェクト設定

1. **Project Name**: `v0-helm-pdca-demo`
2. **Framework Preset**: Next.js（自動検出されるはず）
3. **Root Directory**: `Dev/app/v0-helm-demo` または `.`（リポジトリのルートがフロントエンドの場合）
4. **Build Command**: `pnpm build` または `npm run build`
5. **Output Directory**: `.next`（Next.jsのデフォルト）

#### ステップ3: 環境変数の設定

**この時点で環境変数を設定できます**：

1. **Environment Variables** セクションを開く
2. 以下を追加：
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: `https://helm-api-dsy6lzllhq-an.a.run.app`
   - Environment: Production, Preview, Development すべて

#### ステップ4: デプロイ

**Deploy** ボタンをクリックしてデプロイを開始します。

## ⚙️ デプロイ後の設定

### 1. 環境変数の確認・追加

デプロイ後、環境変数を追加・変更する場合：

1. Vercelダッシュボード → プロジェクト → **Settings** → **Environment Variables**
2. 必要な環境変数を追加
3. **Redeploy** を実行

### 2. カスタムドメインの設定（オプション）

1. **Settings** → **Domains**
2. カスタムドメインを追加（オプション）

### 3. ビルド設定の確認

**Settings** → **General** → **Build & Development Settings** で以下を確認：

- **Framework Preset**: Next.js
- **Build Command**: `pnpm build` または `npm run build`
- **Output Directory**: `.next`
- **Install Command**: `pnpm install` または `npm install`

## 🔍 トラブルシューティング

### 問題1: ビルドエラーが発生する

**確認事項**:
- `package.json` に `build` スクリプトが定義されているか
- 依存関係が正しくインストールされるか
- 環境変数が正しく設定されているか

**解決方法**:
- ビルドログを確認
- ローカルで `pnpm build` を実行してエラーを確認

### 問題2: 環境変数が反映されない

**解決方法**:
- 環境変数を追加した後、**Redeploy** を実行
- 環境変数が正しい環境（Production）に設定されているか確認

### 問題3: API接続エラー

**解決方法**:
- `NEXT_PUBLIC_API_URL` が正しく設定されているか確認
- CORS設定を確認（[FRONTEND_DEPLOY_CHECK.md](./FRONTEND_DEPLOY_CHECK.md) を参照）

## ✅ デプロイ確認チェックリスト

- [ ] Vercel CLIがインストールされている（またはダッシュボードからデプロイ）
- [ ] プロジェクトがデプロイされている
- [ ] 環境変数 `NEXT_PUBLIC_API_URL` が設定されている
- [ ] 本番URLにアクセスできる
- [ ] ページが正常に表示される
- [ ] API接続が正常に動作する

## 📚 参考ドキュメント

- [Vercel CLI Documentation](https://vercel.com/docs/cli)
- [Vercel Deployment Guide](https://vercel.com/docs/deployments/overview)
- [FRONTEND_DEPLOY_CHECK.md](./FRONTEND_DEPLOY_CHECK.md) - デプロイ後の確認手順

---

**初回デプロイが完了したら、[FRONTEND_DEPLOY_CHECK.md](./FRONTEND_DEPLOY_CHECK.md) の手順に従って動作確認を行いましょう！** 🚀
