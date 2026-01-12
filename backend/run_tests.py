"""
テスト実行スクリプト

使用方法:
    python run_tests.py [オプション]

オプション:
    --unit: ユニットテストのみ実行
    --integration: 統合テストのみ実行
    --e2e: エンドツーエンドテストのみ実行
    --all: すべてのテストを実行（デフォルト）
    --coverage: カバレッジレポートを生成
"""

import sys
import subprocess
import argparse


def run_command(cmd, description):
    """コマンドを実行"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"実行コマンド: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="テスト実行スクリプト")
    parser.add_argument("--unit", action="store_true", help="ユニットテストのみ実行")
    parser.add_argument("--integration", action="store_true", help="統合テストのみ実行")
    parser.add_argument("--e2e", action="store_true", help="エンドツーエンドテストのみ実行")
    parser.add_argument("--all", action="store_true", default=True, help="すべてのテストを実行")
    parser.add_argument("--coverage", action="store_true", help="カバレッジレポートを生成")
    
    args = parser.parse_args()
    
    # pytestの基本コマンド
    pytest_cmd = ["pytest"]
    
    if args.coverage:
        pytest_cmd.extend(["--cov=services", "--cov-report=html", "--cov-report=term"])
    
    # テストタイプの指定
    if args.unit:
        pytest_cmd.append("tests/unit/")
        description = "ユニットテストを実行中..."
    elif args.integration:
        pytest_cmd.append("tests/integration/")
        description = "統合テストを実行中..."
        print("\n⚠️  注意: 統合テストを実行するには、バックエンドサーバーが起動している必要があります")
        print("   コマンド: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    elif args.e2e:
        pytest_cmd.append("tests/e2e/")
        description = "エンドツーエンドテストを実行中..."
        print("\n⚠️  注意: エンドツーエンドテストを実行するには、バックエンドサーバーが起動している必要があります")
        print("   コマンド: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    else:
        pytest_cmd.append("tests/")
        description = "すべてのテストを実行中..."
        print("\n⚠️  注意: 統合テストとE2Eテストを実行するには、バックエンドサーバーが起動している必要があります")
        print("   コマンド: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    
    # テスト実行
    success = run_command(pytest_cmd, description)
    
    if success:
        print("\n✅ すべてのテストが成功しました！")
        if args.coverage:
            print("\n📊 カバレッジレポート: htmlcov/index.html")
    else:
        print("\n❌ 一部のテストが失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
