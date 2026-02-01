# Gemini 3 への移行ガイド

このドキュメントは、HelmアプリケーションをGemini 3シリーズ（Gemini 3 Pro / Gemini 3 Flash）に移行するための手順を説明します。

## 参考ドキュメント

- [Gemini 3 デベロッパーガイド](https://ai.google.dev/gemini-api/docs/gemini-3?hl=ja)

## 主な変更点

### 1. モデル名の変更

**旧モデル（Gemini 1.5）:**
- `gemini-1.5-flash`
- `gemini-1.5-flash-001`
- `gemini-1.5-pro`

**新モデル（Gemini 3）:**
- `gemini-3-pro-preview` - 高品質な推論タスク向け
- `gemini-3-flash-preview` - 高速で効率的な推論タスク向け（推奨）

### 2. API仕様の違い

#### Gen AI SDK（google-generativeai）を使用する場合

既存の `google.generativeai` パッケージは引き続き使用可能ですが、モデル名は以下の形式で指定します：

```python
import google.generativeai as genai

# モデル名はプレフィックスなしで指定
model = genai.GenerativeModel("gemini-3-flash-preview")
```

**重要**: Gen AI SDKでは `models/` プレフィックスは不要です。

#### 新しいGen AI SDK（google.genai）を使用する場合

新しいSDKを使用する場合は、以下の形式になります：

```python
from google import genai

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Your prompt here"
)
```

**注意**: 現在のHelmアプリケーションは既存の `google.generativeai` を使用しているため、モデル名の変更のみで対応可能です。

### 3. プロンプト設計の変更

Gemini 3は推論モデルであるため、プロンプトの作成方法が変わります：

- **簡潔な指示**: 冗長なプロンプトエンジニアリングは不要
- **直接的な指示**: 明確で直接的な指示に最適に応答
- **コンテキスト管理**: 大規模なデータセットの場合は、データの後に具体的な指示を配置

詳細は[プロンプトエンジニアリングガイド](https://ai.google.dev/gemini-api/docs/gemini-3?hl=ja#prompt-best-practices)を参照してください。

### 4. 思考レベル（Thinking Level）

Gemini 3では、`thinking_level`パラメータを使用して推論の深さを制御できます：

- `low` - 高速、軽量な推論
- `medium` - バランス型（デフォルト）
- `high` - 深い推論、複雑なタスク向け

**注意**: 現在のコードでは `thinking_level` は使用していませんが、必要に応じて追加可能です。

## 移行手順

### ステップ1: モデル名の更新

環境変数 `LLM_MODEL` を更新：

```powershell
gcloud run services update helm-api `
  --region asia-northeast1 `
  --update-env-vars "LLM_MODEL=gemini-3-flash-preview"
```

または、コードのデフォルト値を更新（既に実施済み）：
- `config.py`: `LLM_MODEL` のデフォルト値を `gemini-3-flash-preview` に変更
- `llm_service.py`: デフォルトモデル名を `gemini-3-flash-preview` に変更

### ステップ2: 再デプロイ

```powershell
cd Dev/backend
.\deploy.ps1
```

### ステップ3: 動作確認

ログを確認して、Gemini 3が正常に動作していることを確認：

```powershell
gcloud run services logs read helm-api --region asia-northeast1 --limit 50 | Select-String -Pattern "LLM|Gen AI|gemini-3" -Context 1
```

期待されるログ：
```
Gen AI SDK呼び出し成功: model=gemini-3-flash-preview, elapsed=X.XXs
✅ LLM分析完了（実際のLLM生成）: overall_score=XX, model=gemini-3-flash-preview
```

## Googleアカウント側の設定

**特別な設定は不要です。** 既存のAPIキー（`GOOGLE_API_KEY`）でGemini 3を使用できます。

ただし、以下の点を確認してください：

1. **APIキーの有効性**: Gemini APIキーが有効であることを確認
2. **使用制限**: Gemini 3 Proには無料枠がないため、課金が発生する可能性があります
   - `gemini-3-flash-preview` には無料枠があります
3. **リージョン**: Gemini 3は利用可能なリージョンが異なる可能性があります

## トラブルシューティング

### エラー: `404 models/gemini-3-flash-preview is not found`

**原因**: モデル名に `models/` プレフィックスが含まれている

**解決方法**: Gen AI SDKではプレフィックスなしで指定してください。コードは既に修正済みです。

### エラー: `API version v1beta` に関するエラー

**原因**: 古いAPIバージョンを使用している

**解決方法**: `google-generativeai` パッケージを最新版に更新：

```bash
pip install --upgrade google-generativeai
```

現在のバージョン: `google-generativeai==0.8.3`

### モデルが利用できない

**確認事項**:
1. APIキーが正しく設定されているか
2. モデル名が正しいか（`gemini-3-flash-preview` または `gemini-3-pro-preview`）
3. リージョンがサポートされているか

## 参考情報

- [Gemini 3 デベロッパーガイド](https://ai.google.dev/gemini-api/docs/gemini-3?hl=ja)
- [Gemini API モデル一覧](https://ai.google.dev/gemini-api/docs/models/gemini)
- [Gen AI SDK ドキュメント](https://ai.google.dev/gemini-api/docs/libraries)

---

**移行完了後、フロントエンドから再度テストして、Gemini 3が正常に動作していることを確認してください。**
