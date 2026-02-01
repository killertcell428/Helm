# 🔐 APIキー置き換えガイド

このドキュメントは、漏洩したAPIキーを新しいAPIキーに置き換える手順を説明します。

## ⚠️ 重要事項

**漏洩したAPIキーは即座に無効化してください。**
- Google AI Studioで古いAPIキーを削除または無効化
- 新しいAPIキーを生成して使用

## 📋 手順

### ステップ1: 新しいAPIキーの取得

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. 「APIキーを作成」をクリック
4. 新しいAPIキーをコピー（**すぐに使用するため、安全な場所に保存**）

### ステップ2: 古いAPIキーの無効化（重要）

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. 漏洩したAPIキー（`AIzaSyCnf9uZEpMZSMK8fxRzIfhER1LI6ABujPQ`）を探す
3. 「削除」または「無効化」をクリック

**注意**: 古いAPIキーを無効化すると、現在のCloud Runサービスも動作しなくなります。新しいAPIキーを設定してから無効化することを推奨します。

### ステップ3: Cloud Run環境変数の更新

新しいAPIキーをCloud Runサービスに設定します。

#### 方法1: PowerShellスクリプトを使用（推奨）

```powershell
cd Dev/docs/gcloud
.\set_env_vars.ps1
```

スクリプトが新しいAPIキーの入力を求めます。新しいAPIキーを入力してください。

#### 方法2: コマンドラインから直接設定

```powershell
# 新しいAPIキーを環境変数に設定（セキュリティのため、直接コマンドに含めない）
$newApiKey = Read-Host "新しいGemini APIキーを入力してください"

# Cloud Run環境変数を更新
gcloud run services update helm-api `
  --region asia-northeast1 `
  --update-env-vars "GOOGLE_API_KEY=$newApiKey"
```

#### 方法3: Google Cloud Consoleから設定（最も安全）

1. [Cloud Runコンソール](https://console.cloud.google.com/run?project=helm-project-484105) にアクセス
2. `helm-api` サービスをクリック
3. 「編集と新しいリビジョンをデプロイ」をクリック
4. 「変数とシークレット」タブを開く
5. `GOOGLE_API_KEY` 環境変数を探し、編集アイコン（鉛筆マーク）をクリック
6. 値を新しいAPIキーに変更
7. 「保存」をクリック
8. ページ下部の「デプロイ」をクリック

### ステップ4: 動作確認

新しいAPIキーが正しく設定されているか確認します。

```powershell
# 環境変数を確認（APIキーは表示されませんが、設定されているか確認できます）
gcloud run services describe helm-api `
  --region asia-northeast1 `
  --format="value(spec.template.spec.containers[0].env)" | Select-String "GOOGLE_API_KEY"
```

### ステップ5: APIの動作確認

実際にAPIが正常に動作しているか確認します。

```powershell
# ログを確認して、LLMが正常に動作しているか確認
gcloud run services logs read helm-api --region asia-northeast1 --limit 50 | Select-String -Pattern "LLM|Gen AI|gemini-3" -Context 1
```

期待されるログ：
```
Gen AI SDK呼び出し成功: model=gemini-3-flash-preview, elapsed=X.XXs
✅ LLM分析完了（実際のLLM生成）: overall_score=XX, model=gemini-3-flash-preview
```

**エラーが表示されないこと**を確認してください。もし `403 Your API key was reported as leaked` というエラーが表示される場合は、まだ古いAPIキーが使用されている可能性があります。

### ステップ6: フロントエンドでの動作確認

フロントエンドからAPIを呼び出して、正常に動作することを確認します。

1. フロントエンド（https://v0-helm-pdca-demo.vercel.app）にアクセス
2. Case1デモページでパターンを選択
3. 「データ取得」→「Helm分析」を実行
4. 実際のLLM生成結果が返されることを確認

## 🔒 セキュリティのベストプラクティス

### APIキーの管理

1. **環境変数として管理**: APIキーはコードに直接書かず、環境変数として管理
2. **`.gitignore`に追加**: `.env`ファイルやAPIキーを含むファイルを`.gitignore`に追加
3. **Git履歴の確認**: もしAPIキーがGit履歴に含まれている場合は、履歴を書き換える必要があります
   ```bash
   # Git履歴からAPIキーを削除（注意: これは履歴を書き換えます）
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch Dev/docs/gcloud/set_env_vars.ps1 Dev/docs/gcloud/DEPLOY_SUCCESS_NEXT_STEPS.md" \
     --prune-empty --tag-name-filter cat -- --all
   ```

### 今後の対策

1. **プレースホルダーの使用**: ドキュメントやスクリプトでは、実際のAPIキーではなく `YOUR_API_KEY_HERE` のようなプレースホルダーを使用
2. **環境変数の確認**: デプロイ前に、コードやドキュメントにAPIキーが含まれていないか確認
3. **GitHub Secretsの使用**: GitHub Actionsを使用する場合は、GitHub Secretsを使用してAPIキーを管理

## 📝 チェックリスト

- [ ] 新しいAPIキーを取得
- [ ] 新しいAPIキーをCloud Run環境変数に設定
- [ ] 動作確認（ログでエラーがないことを確認）
- [ ] フロントエンドでの動作確認
- [ ] 古いAPIキーを無効化（動作確認後）
- [ ] Git履歴からAPIキーを削除（必要に応じて）

## 🆘 トラブルシューティング

### エラー: `403 Your API key was reported as leaked`

**原因**: まだ古いAPIキーが使用されている、または新しいAPIキーが正しく設定されていない

**解決方法**:
1. Cloud Run環境変数を確認
2. 新しいAPIキーが正しく設定されているか確認
3. デプロイが完了しているか確認（環境変数を変更した場合は新しいリビジョンがデプロイされる必要があります）

### エラー: `404 model not found`

**原因**: モデル名が間違っている、またはAPIキーが無効

**解決方法**:
1. モデル名が `gemini-3-flash-preview` であることを確認
2. APIキーが有効であることを確認

---

**新しいAPIキーの設定が完了したら、フロントエンドから再度テストしてください！** 🚀
