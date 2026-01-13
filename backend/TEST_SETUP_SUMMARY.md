# テスト実行サマリー（E2E / パフォーマンス）

このドキュメントは、Helm バックエンドのテスト実行方法をまとめたものです。

## 前提条件

- バックエンドサーバーが起動していること:

```bash
cd Dev/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- テスト用依存関係がインストールされていること:

```bash
cd Dev/backend
pip install -r requirements_test.txt
```

## テストカテゴリ

### 1. ユニットテスト

- 対象: スコアリング、分析、エスカレーションロジックなど
- 実行コマンド:

```bash
cd Dev/backend
pytest tests/unit -m unit -v
```

### 2. 統合テスト

- 対象: APIエンドポイント、Google API統合など
- 実行コマンド:

```bash
cd Dev/backend
pytest tests/integration -m integration -v
```

### 3. エンドツーエンドテスト（E2E）

- 対象: 会議取り込み → 分析 → エスカレーション → 承認 → 実行 → 結果取得 までの完全フロー
- テストファイル: `tests/e2e/test_full_flow.py`
- 主なテスト:
  - `test_complete_flow`
  - `test_complete_flow_with_websocket_progress`（WebSocket進捗確認付き）

#### 実行コマンド

```bash
cd Dev/backend
pytest tests/e2e -m e2e -v
```

特に WebSocket を含むテストだけを実行したい場合:

```bash
cd Dev/backend
pytest tests/e2e -m "e2e and websocket" -v
```

### 4. パフォーマンステスト（軽量）

> 目的: 主要APIとWebSocketフローのレイテンシをざっくり把握すること  
> ※しきい値による fail は行わず、ログ出力を中心とした「計測用」です。

- テストファイル:
  - `tests/perf/test_api_latency.py`
  - `tests/perf/test_websocket_latency.py`

#### 実行コマンド

すべてのパフォーマンステストを実行:

```bash
cd Dev/backend
pytest tests/perf -m slow -v
```

特定のテストのみを実行する例:

```bash
cd Dev/backend
pytest tests/perf/test_api_latency.py::test_api_latency_analyze -v
pytest tests/perf/test_websocket_latency.py::test_websocket_latency_progress_and_completed -v
```

## 補足

- WebSocket 関連テストでは `websockets` パッケージが必要です。`requirements_test.txt` に含まれています。
- 本番用の CI では、ユニットテスト・統合テストを中心に実行し、E2E/パフォーマンスは手動または別ジョブでの実行を想定しています。

