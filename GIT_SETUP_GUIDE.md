# Git・GitHub連携ガイド（初心者向け）

このガイドでは、DevディレクトリでGitを初期化し、GitHubに連携する手順を説明します。

## ✅ 完了した作業

1. ✅ Gitリポジトリの初期化（`git init`）
2. ✅ `.gitignore`ファイルの作成（機密情報や不要なファイルを除外）
3. ✅ 初回コミット（`Initial commit: Dev directory setup`）

## 📋 次のステップ：GitHubへの連携

### ステップ1: GitHubでリポジトリを作成

1. **GitHubにログイン**
   - https://github.com にアクセス
   - アカウントにログイン（アカウントがない場合は作成）

2. **新しいリポジトリを作成**
   - 右上の「+」ボタンをクリック → 「New repository」を選択
   - リポジトリ名を入力（例：`Google-PJ-Dev`）
   - **重要：** 「Initialize this repository with a README」のチェックは**外す**（既にローカルにファイルがあるため）
   - 「Public」または「Private」を選択
   - 「Create repository」をクリック

3. **リポジトリURLをコピー**
   - 作成後、表示されるページでリポジトリのURLをコピー
   - 例：`https://github.com/あなたのユーザー名/Google-PJ-Dev.git`

### ステップ2: ローカルリポジトリをGitHubに接続

PowerShellまたはGit Bashで以下のコマンドを実行します：

```powershell
# Devディレクトリに移動
cd c:\Users\uecha\Project_P\Personal\Google-PJ\Dev

# GitHubリポジトリをリモートとして追加
# （以下のURLは、ステップ1でコピーした実際のURLに置き換えてください）
git remote add origin https://github.com/あなたのユーザー名/Google-PJ-Dev.git

# 現在のブランチ名を確認（通常はmasterまたはmain）
git branch

# ブランチ名がmasterの場合は、mainに変更（GitHubの標準に合わせる）
git branch -M main

# GitHubにプッシュ（初回）
git push -u origin main
```

**注意：** ブランチ名が`master`の場合は、上記の`git branch -M main`で`main`に変更してからプッシュしてください。

### ステップ3: 認証

初回プッシュ時に認証が求められます：

- **Personal Access Token（推奨）**
  1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  2. 「Generate new token (classic)」をクリック
  3. スコープで`repo`にチェック
  4. トークンを生成してコピー
  5. パスワードの代わりにこのトークンを入力

- **Git Credential Manager（Windows）**
  - 初回はブラウザで認証画面が開く場合があります

## 🔄 今後の作業フロー

### ファイルを変更した後

```powershell
# 変更を確認
git status

# 変更をステージング（追加）
git add .

# または特定のファイルのみ追加
git add ファイル名

# コミット（変更内容を記録）
git commit -m "変更内容の説明"

# GitHubにプッシュ（アップロード）
git push
```

### よく使うコマンド

```powershell
# 現在の状態を確認
git status

# 変更履歴を確認
git log

# リモートリポジトリの確認
git remote -v

# 最新の変更を取得（他の人が変更した場合）
git pull
```

## ⚠️ 注意事項

1. **機密情報はコミットしない**
   - `.gitignore`に含まれているファイル（`.env`、認証情報のJSONファイルなど）は自動的に除外されます
   - 誤って機密情報をコミットした場合は、すぐにGitHubで削除してください

2. **コミットメッセージは分かりやすく**
   - 何を変更したかが分かるように、日本語で説明を書くことを推奨します
   - 例：`git commit -m "バックエンドAPIのエラーハンドリングを改善"`

3. **定期的にコミット・プッシュ**
   - 作業が一段落したら、こまめにコミット・プッシュすることをお勧めします
   - バックアップの役割も果たします

## 🆘 トラブルシューティング

### エラー：`remote origin already exists`
```powershell
# 既存のリモートを削除してから再追加
git remote remove origin
git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git
```

### エラー：`failed to push some refs`
```powershell
# GitHubに既にファイルがある場合、先に取得してからプッシュ
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### 認証エラーが続く場合
- Personal Access Tokenを再生成
- Git Credential Managerをクリア：
  ```powershell
  git credential-manager-core erase
  ```

## 📚 参考リンク

- [Git公式ドキュメント](https://git-scm.com/doc)
- [GitHub公式ドキュメント](https://docs.github.com/ja)
- [GitHub CLI（コマンドラインからリポジトリ作成も可能）](https://cli.github.com/)

---

**質問や問題があれば、このドキュメントを参照してください！**
