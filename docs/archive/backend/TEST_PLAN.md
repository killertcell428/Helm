# テスト計画書

## 目的

Week 2までに実装したアプリケーションの動作確認とテストを実施し、品質を保証する。

## テスト範囲

### 1. ユニットテスト

#### 1.1 ScoringService (`services/scoring.py`)
- [x] 重要性スコアの計算
- [x] 緊急度スコアの計算
- [x] 総合スコアの計算
- [x] 説明可能な理由生成
- [x] パターン別評価ロジック（正当化フェーズ、判断集中、反対意見無視など）

#### 1.2 StructureAnalyzer (`services/analyzer.py`)
- [x] ルールベース分析
- [x] KPI下方修正の検出
- [x] 正当化フェーズの検出
- [x] 判断集中率の計算
- [x] 反対意見無視の検出
- [x] スコアリングサービスとの連携

#### 1.3 EscalationEngine (`services/escalation_engine.py`)
- [x] エスカレーション判断ロジック
- [x] エスカレーション理由生成
- [x] 閾値チェック（70点）
- [x] 重要度チェック（HIGH/CRITICAL）

### 2. 統合テスト（APIエンドポイント）

#### 2.1 データ取り込み
- [x] `/api/meetings/ingest` - 議事録取り込み
- [x] `/api/chat/ingest` - チャット取り込み

#### 2.2 分析
- [x] `/api/analyze` - 構造的問題検知
- [x] `/api/analysis/{analysis_id}` - 分析結果取得

#### 2.3 エスカレーション
- [x] `/api/escalate` - Executive呼び出し

#### 2.4 承認
- [x] `/api/approve` - Executive承認

#### 2.5 実行
- [x] `/api/execute` - AI自律実行開始
- [x] `/api/execution/{execution_id}` - 実行状態取得
- [x] `/api/execution/{execution_id}/results` - 実行結果取得

#### 2.6 ダウンロード
- [x] `/api/download/{file_id}` - ファイルダウンロードURL取得

### 3. エンドツーエンドテスト

#### 3.1 完全なフロー
1. 議事録取り込み
2. チャット取り込み
3. 構造的問題検知
4. エスカレーション
5. Executive承認
6. AI自律実行
7. 結果取得

#### 3.2 エラーハンドリング
- [x] 存在しないリソースへのアクセス
- [x] 無効なリクエストデータ
- [x] サービスエラー時のフォールバック

## テスト環境

- **Python**: 3.11以上
- **テストフレームワーク**: pytest
- **テストランナー**: pytest
- **カバレッジ**: pytest-cov（オプション）

## テスト実行方法

### 1. 依存関係のインストール

```bash
cd Dev/backend
pip install -r requirements_minimal.txt
pip install pytest pytest-asyncio httpx
```

### 2. ユニットテストの実行

```bash
pytest tests/unit/ -v
```

### 3. 統合テストの実行

```bash
# バックエンドサーバーを起動
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 別のターミナルでテスト実行
pytest tests/integration/ -v
```

### 4. エンドツーエンドテストの実行

```bash
# バックエンドサーバーを起動
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 別のターミナルでテスト実行
pytest tests/e2e/ -v
```

### 5. すべてのテストを実行

```bash
pytest tests/ -v
```

### 6. 既存の動作確認スクリプト

```bash
python test_mock_services.py
```

## テストデータ

テスト用のモックデータは各サービスに実装済みです。

## 期待される結果

- すべてのユニットテストが成功
- すべての統合テストが成功
- エンドツーエンドフローが正常に動作
- エラーハンドリングが適切に機能

## 次のステップ

テスト完了後：
1. テスト結果のレビュー
2. 失敗したテストの修正
3. カバレッジレポートの確認
4. 実API実装への移行準備
