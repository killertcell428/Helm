# 実API実装計画

## 概要

モック実装から実際のGoogle API統合への移行計画です。コーディングで実装できる部分と、ユーザーに依頼する部分を明確に分けています。

## 実装の優先順位

1. **Google Drive API** - ファイル保存・ダウンロード（最重要）
2. **Google Docs API** - 資料作成
3. **Google Chat API** - チャット取得
4. **Google Meet API** - 議事録取得

## ステップ1: Google Drive API実装

### 📋 ユーザー作業（事前準備）

以下の作業をGoogle Cloud Consoleで実施してください：

1. **Google Cloud Projectの作成**
   - [Google Cloud Console](https://console.cloud.google.com/) にアクセス
   - 新しいプロジェクトを作成（または既存のプロジェクトを使用）
   - プロジェクトIDをメモ

2. **Google Drive APIの有効化**
   - APIとサービス > ライブラリ
   - "Google Drive API"を検索して有効化

3. **サービスアカウントの作成**
   - IAMと管理 > サービスアカウント
   - 「サービスアカウントを作成」をクリック
   - 名前: `helm-drive-service`
   - 説明: `Helm Google Drive API用サービスアカウント`
   - 「作成して続行」をクリック

4. **権限の付与**
   - ロール: `Google Drive API > ドライブ API ユーザー` を選択
   - 「完了」をクリック

5. **認証情報（JSON）のダウンロード**
   - 作成したサービスアカウントをクリック
   - 「キー」タブ > 「キーを追加」> 「新しいキーを作成」
   - キーのタイプ: `JSON`
   - 「作成」をクリック
   - ダウンロードされたJSONファイルを安全な場所に保存
   - **重要**: このファイルは秘密情報です。Gitにコミットしないでください

6. **環境変数の設定**
   - ダウンロードしたJSONファイルのパスを環境変数に設定
   ```bash
   # Windows PowerShell
   $env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\credentials.json"
   $env:GOOGLE_CLOUD_PROJECT_ID="your-project-id"
   
   # または .env ファイルに追加
   GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\credentials.json
   GOOGLE_CLOUD_PROJECT_ID=your-project-id
   ```

### 💻 コーディング実装（開発者作業）

以下のファイルを実装します：

- `services/google_drive.py` - Google Drive API統合
- 認証処理の実装
- ファイルアップロード機能
- ファイルダウンロード機能
- エラーハンドリング
- モック/実APIの自動切り替え

**実装完了の確認方法**:
- 環境変数が設定されている場合、実APIを使用
- 環境変数が設定されていない場合、モックに自動フォールバック

---

## ステップ2: Google Docs API実装

### 📋 ユーザー作業（事前準備）

1. **Google Docs APIの有効化**
   - APIとサービス > ライブラリ
   - "Google Docs API"を検索して有効化

2. **サービスアカウントへの権限追加**
   - ステップ1で作成したサービスアカウントに以下を追加：
     - ロール: `Google Docs API > ドキュメント API ユーザー`

### 💻 コーディング実装（開発者作業）

- `services/google_workspace.py` - Google Docs API統合
- ドキュメント作成機能
- コンテンツ挿入機能
- エラーハンドリング

---

## ステップ3: Google Chat API実装

### 📋 ユーザー作業（事前準備）

1. **Google Chat APIの有効化**
   - APIとサービス > ライブラリ
   - "Google Chat API"を検索して有効化

2. **サービスアカウントへの権限追加**
   - ロール: `Google Chat API > Chat API ユーザー`

3. **ドメイン全体の委任（必要に応じて）**
   - Google Workspace管理者による設定が必要な場合があります
   - 詳細は[Google Chat API ドキュメント](https://developers.google.com/chat/api/guides/auth)を参照

### 💻 コーディング実装（開発者作業）

- `services/google_chat.py` - Google Chat API統合
- メッセージ取得機能
- チャンネル情報取得機能
- エラーハンドリング

---

## ステップ4: Google Meet API実装

### 📋 ユーザー作業（事前準備）

1. **Google Meet APIの有効化**
   - APIとサービス > ライブラリ
   - "Google Meet API"を検索して有効化

2. **サービスアカウントへの権限追加**
   - ロール: `Google Meet API > Meet API ユーザー`

3. **注意事項**
   - Google Meet APIは制限が厳しい場合があります
   - 議事録の取得には特別な権限が必要な場合があります

### 💻 コーディング実装（開発者作業）

- `services/google_meet.py` - Google Meet API統合
- 議事録取得機能
- 会議情報取得機能
- エラーハンドリング

---

## 実装の進め方

### 各ステップの流れ

1. **ユーザー作業完了の確認**
   - 環境変数が設定されているか確認
   - 認証情報ファイルが存在するか確認

2. **コーディング実装**
   - 実API統合コードを実装
   - モック/実APIの自動切り替えを実装
   - エラーハンドリングを実装

3. **テスト**
   - 実APIが正しく動作するか確認
   - モックへのフォールバックが動作するか確認

4. **次のステップへ**

### 実装チェックリスト

各API実装時に以下を確認：

- [ ] 認証処理が正しく実装されている
- [ ] モック/実APIの自動切り替えが動作する
- [ ] エラーハンドリングが適切に実装されている
- [ ] 環境変数が設定されていない場合、モックにフォールバックする
- [ ] ログ出力が適切に実装されている
- [ ] テストが追加されている（可能な範囲で）

---

## トラブルシューティング

### 認証エラー

**症状**: `google.auth.exceptions.DefaultCredentialsError`

**解決方法**:
1. 環境変数 `GOOGLE_APPLICATION_CREDENTIALS` が正しく設定されているか確認
2. 認証情報ファイルのパスが正しいか確認
3. 認証情報ファイルが有効か確認（JSON形式が正しいか）

### API有効化エラー

**症状**: `googleapiclient.errors.HttpError: 403 Forbidden`

**解決方法**:
1. Google Cloud Consoleで、必要なAPIが有効化されているか確認
2. サービスアカウントに適切な権限が付与されているか確認

### 権限エラー

**症状**: `googleapiclient.errors.HttpError: 403 Permission denied`

**解決方法**:
1. サービスアカウントに適切なIAMロールが付与されているか確認
2. ドメイン全体の委任が必要な場合、Google Workspace管理者に依頼

---

## 次のステップ

実装が完了したら：

1. 各APIの動作確認
2. エラーハンドリングの強化
3. ログ出力の改善
4. パフォーマンス最適化
5. テストの追加

---

## 参考リンク

- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Drive API ドキュメント](https://developers.google.com/drive/api)
- [Google Docs API ドキュメント](https://developers.google.com/docs/api)
- [Google Chat API ドキュメント](https://developers.google.com/chat/api)
- [Google Meet API ドキュメント](https://developers.google.com/meet/api)
