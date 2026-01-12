# トラブルシューティングガイド

## 依存関係のインストールエラー

### pydantic-core のインストールエラー

**エラー内容:**
```
error: metadata-generation-failed
× Encountered error while generating package metadata.
╰─> pydantic-core
Cargo, the Rust package manager, is not installed or is not on PATH.
```

**原因:**
- `pydantic-core` の古いバージョンがRustのコンパイルを必要とする
- Windows環境で特に発生しやすい

**解決方法:**

1. **最小限の依存関係を使用（推奨）**
   ```bash
   pip install -r requirements_minimal.txt
   ```
   これでFastAPIと基本的な機能は動作します。

2. **pydanticの最新版を使用**
   ```bash
   pip install --upgrade pydantic
   ```
   最新版にはpre-built wheelが含まれているため、Rustのコンパイルが不要です。

3. **Rustをインストール（上級者向け）**
   - [Rust公式サイト](https://rustup.rs/) からRustをインストール
   - インストール後、再度 `pip install -r requirements.txt` を実行

### Google Cloudライブラリのインストールエラー

**エラー内容:**
```
ERROR: Could not find a version that satisfies the requirement google-cloud-xxx
```

**解決方法:**
- 現在はモックデータを使用しているため、Google Cloudライブラリは不要です
- `requirements_minimal.txt` を使用してください

## サーバー起動エラー

### uvicorn: command not found

**原因:**
- 仮想環境が有効になっていない
- 依存関係がインストールされていない

**解決方法:**
```bash
# 仮想環境を有効化
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 依存関係を再インストール
pip install -r requirements_minimal.txt
```

### Address already in use

**原因:**
- ポート8000が既に使用されている

**解決方法:**
```bash
# 別のポートを使用
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

フロントエンドの `.env.local` も更新してください：
```
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### ModuleNotFoundError

**エラー内容:**
```
ModuleNotFoundError: No module named 'services'
```

**原因:**
- カレントディレクトリが間違っている
- Pythonパスが正しく設定されていない

**解決方法:**
```bash
# backendディレクトリにいることを確認
cd Dev/backend

# サーバーを起動
uvicorn main:app --reload
```

## API接続エラー

### CORSエラー

**エラー内容（ブラウザコンソール）:**
```
Access to fetch at 'http://localhost:8000/api/...' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**解決方法:**
1. バックエンドの `main.py` のCORS設定を確認
2. フロントエンドのURLが許可されているか確認
3. バックエンドを再起動

### Connection refused

**エラー内容:**
```
Failed to fetch
ERR_CONNECTION_REFUSED
```

**解決方法:**
1. バックエンドが起動しているか確認
2. ポート番号が正しいか確認（デフォルト: 8000）
3. `.env.local` の `NEXT_PUBLIC_API_URL` が正しいか確認

### 404 Not Found

**エラー内容:**
```
404: Not Found
```

**解決方法:**
1. APIエンドポイントのURLが正しいか確認
2. バックエンドのログでエラーメッセージを確認
3. APIドキュメント（http://localhost:8000/docs）でエンドポイントを確認

## データが表示されない

### 分析結果が表示されない

**原因:**
- モックデータが正しく生成されていない
- API呼び出しが失敗している

**解決方法:**
1. ブラウザの開発者ツール（F12）でネットワークタブを確認
2. APIリクエストが成功しているか確認
3. レスポンスデータを確認

### 実行進捗が更新されない

**原因:**
- バックグラウンドタスクが実装されていない（現在はモック）

**解決方法:**
- 現在はモックデータを使用しているため、進捗は自動的に更新されます
- 実際の実装では、バックグラウンドタスクが必要です

## パフォーマンス問題

### サーバーの起動が遅い

**原因:**
- 依存関係のインストールが不完全
- 仮想環境の問題

**解決方法:**
```bash
# 仮想環境を再作成
deactivate  # 仮想環境を無効化
rm -rf venv    # 仮想環境を削除（Mac/Linux）
rmdir /s venv  # 仮想環境を削除（Windows）

# 新しい仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements_minimal.txt
```

### APIレスポンスが遅い

**原因:**
- モックデータの生成処理
- ネットワークの問題

**解決方法:**
- 現在はモックデータを使用しているため、実際の処理は高速です
- 本番環境では、キャッシュや最適化を実装予定

## よくある質問

**Q: requirements.txt と requirements_minimal.txt の違いは？**
A: `requirements.txt` にはGoogle Cloudライブラリが含まれていますが、`requirements_minimal.txt` には基本的な依存関係のみが含まれています。現在はモックデータを使用しているため、`requirements_minimal.txt` で十分です。

**Q: Windowsでインストールエラーが発生します**
A: `requirements_minimal.txt` を使用してください。これにはpre-built wheelが含まれているため、コンパイルが不要です。

**Q: 実際のGoogleサービスを使用するには？**
A: `requirements.txt` をインストールし、Google Cloud認証情報を設定する必要があります。詳細は [SETUP.md](./SETUP.md) を参照してください。

## サポート

問題が解決しない場合は、以下を確認してください：

1. [クイックスタートガイド](../QUICKSTART.md) のトラブルシューティングセクション
2. [APIドキュメント](./API_DOCUMENTATION.md) でAPIの使用方法を確認
3. ブラウザの開発者ツールでエラーメッセージを確認

