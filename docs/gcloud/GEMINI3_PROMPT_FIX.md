# Gemini 3 Flash Preview プロンプト最適化

Gemini 3 Flash Previewに変更したことで、プロンプトの相性が悪くなり、エスカレーション時にデータが正しく取得できなくなる問題が発生しました。

## 問題の原因

1. **エスカレーション時のスコア取得ロジック**: `analysis.get("score", 0)`を最初に参照していたため、`overall_score`が正しく取得できていなかった
2. **プロンプトの冗長性**: Gemini 3は推論モデルで「簡潔な指示」を好むため、現在のプロンプトが冗長すぎる可能性

## 修正内容

### 1. エスカレーション時のスコア取得ロジックの修正

**修正前**:
```python
score = analysis.get("score", 0)  # scoreを最初に参照
if score == 0:
    ensemble = analysis.get("ensemble", {})
    if isinstance(ensemble, dict):
        score = ensemble.get("overall_score", 0)
```

**修正後**:
```python
# 優先順位: overall_score > score > ensemble.overall_score
score = analysis.get("overall_score", 0)  # overall_scoreを最初に参照
if score == 0:
    score = analysis.get("score", 0)
if score == 0:
    ensemble = analysis.get("ensemble", {})
    if isinstance(ensemble, dict):
        score = ensemble.get("overall_score", 0)
```

### 2. プロンプトの簡潔化

Gemini 3 Flash Previewは推論モデルであるため、プロンプトを簡潔にしました：

**修正前**: 冗長な説明と複数のセクション

**修正後**: 
- 簡潔な役割説明
- 明確な評価原則（健全な意思決定 vs 構造的問題）
- JSON形式の出力例を明確化

### 3. スコアの型変換

文字列として返される可能性があるため、数値への変換を追加：

```python
# スコアを数値に変換（文字列の場合に対応）
try:
    overall_score = int(float(overall_score))
except (ValueError, TypeError):
    overall_score = 0
```

## 修正ファイル

1. `Dev/backend/main.py`: エスカレーションエンドポイントのスコア取得ロジックを修正
2. `Dev/backend/services/escalation_engine.py`: エスカレーションエンジンのスコア取得ロジックを修正
3. `Dev/backend/services/prompts/analysis_prompt.py`: プロンプトを簡潔化

## 再デプロイ

修正後、再デプロイしてください：

```powershell
cd Dev/backend
.\deploy.ps1
```

## 動作確認

再デプロイ後、以下の点を確認：

1. **LLM分析結果**: `overall_score=25`が正しく返されているか
2. **エスカレーション**: スコアが正しく取得され、エスカレーションが正常に動作するか
3. **findings**: ルールベース分析のfindingsが正しく反映されているか

## 参考

- [Gemini 3 デベロッパーガイド](https://ai.google.dev/gemini-api/docs/gemini-3?hl=ja)
- [プロンプトエンジニアリングガイド](https://ai.google.dev/gemini-api/docs/gemini-3?hl=ja#prompt-best-practices)

---

**修正後、フロントエンドから再度テストして、エスカレーションが正常に動作することを確認してください。**
