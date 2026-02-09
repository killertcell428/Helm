# テスト実行ガイド

## 概要

このドキュメントでは、Week 2までに実装したアプリケーションのテスト実行方法を説明します。

## テストの種類

### 1. ユニットテスト
- **場所**: `tests/unit/`
- **対象**: 個別のサービス（ScoringService, StructureAnalyzer, EscalationEngine）
- **実行時間**: 数秒
- **前提条件**: なし（サーバー不要）

### 2. 統合テスト
- **場所**: `tests/integration/`
- **対象**: APIエンドポイント
- **実行時間**: 数十秒
- **前提条件**: バックエンドサーバーが起動している必要があります

### 3. エンドツーエンドテスト
- **場所**: `tests/e2e/`
- **対象**: 完全なフロー（議事録取り込み → 分析 → エスカレーション → 承認 → 実行）
- **実行時間**: 1-2分
- **前提条件**: バックエンドサーバーが起動している必要があります

### 4. 動作確認スクリプト
- **場所**: `test_mock_services.py`
- **対象**: Googleサービス統合（モック）
- **実行時間**: 数十秒
- **前提条件**: バックエンドサーバーが起動している必要があります

## セットアップ

### 1. 依存関係のインストール

```bash
cd Dev/backend
pip install -r requirements_test.txt
```

または、既に`requirements_minimal.txt`をインストールしている場合：

```bash
pip install pytest pytest-asyncio httpx
```

### 2. バックエンドサーバーの起動（統合テスト・E2Eテスト用）

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## テスト実行方法

### 方法1: pytestを直接使用

#### すべてのテストを実行
```bash
pytest tests/ -v
```

#### ユニットテストのみ実行
```bash
pytest tests/unit/ -v
```

#### 統合テストのみ実行
```bash
# バックエンドサーバーを起動してから
pytest tests/integration/ -v
```

#### エンドツーエンドテストのみ実行
```bash
# バックエンドサーバーを起動してから
pytest tests/e2e/ -v
```

### 方法2: テスト実行スクリプトを使用

```bash
# すべてのテストを実行
python run_tests.py

# ユニットテストのみ
python run_tests.py --unit

# 統合テストのみ
python run_tests.py --integration

# エンドツーエンドテストのみ
python run_tests.py --e2e

# カバレッジレポート付き
python run_tests.py --coverage
```

### 方法3: 既存の動作確認スクリプト

```bash
# バックエンドサーバーを起動してから
python test_mock_services.py
```

## テスト結果の確認

### 成功例
```
tests/unit/test_scoring.py::TestScoringService::test_evaluate_justification_phase PASSED
tests/unit/test_scoring.py::TestScoringService::test_evaluate_decision_concentration PASSED
...
======================== 15 passed in 2.34s ========================
```

### 失敗例
```
tests/unit/test_scoring.py::TestScoringService::test_evaluate_justification_phase FAILED
...
FAILED tests/unit/test_scoring.py::TestScoringService::test_evaluate_justification_phase
```

## トラブルシューティング

### 1. サーバーに接続できない（統合テスト・E2Eテスト）

**エラー**: `pytest.skip("バックエンドサーバーに接続できません")`

**解決方法**:
1. バックエンドサーバーが起動しているか確認
2. ポート8000が使用可能か確認
3. ファイアウォール設定を確認

### 2. モジュールが見つからない

**エラー**: `ModuleNotFoundError: No module named 'services'`

**解決方法**:
```bash
# バックエンドディレクトリに移動
cd Dev/backend

# 仮想環境をアクティベート
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
```

### 3. 依存関係が不足している

**エラー**: `ModuleNotFoundError: No module named 'pytest'`

**解決方法**:
```bash
pip install -r requirements_test.txt
```

## カバレッジレポート

カバレッジレポートを生成する場合：

```bash
pytest --cov=services --cov-report=html --cov-report=term tests/
```

レポートは`htmlcov/index.html`に生成されます。

## テストの追加

新しいテストを追加する場合：

1. 適切なディレクトリにテストファイルを作成（`test_*.py`）
2. テストクラス名は`Test*`で始める
3. テストメソッド名は`test_*`で始める
4. `conftest.py`のフィクスチャを活用

例：
```python
# tests/unit/test_new_service.py
class TestNewService:
    def test_new_feature(self):
        # テストコード
        pass
```

## 次のステップ

テスト完了後：
1. テスト結果のレビュー
2. 失敗したテストの修正
3. カバレッジレポートの確認
4. 実API実装への移行準備
