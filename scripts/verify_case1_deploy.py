#!/usr/bin/env python3
"""Case1 デモ デプロイ前検証スクリプト"""
import requests
import subprocess
import sys
from pathlib import Path

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"


def main():
    print("\n=== Case1 デプロイ前検証 ===\n")

    # 1. バックエンド
    print("[1/4] バックエンドヘルスチェック...")
    try:
        r = requests.get(f"{BACKEND_URL}/", timeout=5)
        if r.status_code == 200:
            print("  OK: バックエンドは起動しています")
        else:
            print(f"  NG: ステータス {r.status_code}")
            return 1
    except requests.exceptions.RequestException:
        print("  NG: バックエンドに接続できません。uvicorn main:app --reload --host 0.0.0.0 --port 8000 で起動")
        return 1

    # 2. フロントエンド（オプション: 未起動でもAPIテストは継続）
    print("\n[2/4] フロントエンドヘルスチェック...")
    try:
        r = requests.get(f"{FRONTEND_URL}/", timeout=5)
        if r.status_code == 200:
            print("  OK: フロントエンドは起動しています")
        else:
            print(f"  WARN: ステータス {r.status_code} (pnpm dev で起動)")
    except requests.exceptions.RequestException:
        print("  WARN: フロントエンドに接続できません (pnpm dev で起動してブラウザ検証)")

    # 3. Case1ページ（フロントエンド起動時のみ）
    print("\n[3/4] Case1ページ確認...")
    try:
        r = requests.get(f"{FRONTEND_URL}/demo/case1", timeout=5)
        if r.status_code == 200 and "Case 1" in r.text:
            print("  OK: /demo/case1 が正常に応答しています")
        else:
            print("  WARN: Case1ページの応答が不正")
    except requests.exceptions.RequestException:
        print("  WARN: Case1ページにアクセスできません (フロントエンド未起動)")

    # 4. Case1 API統合テスト
    print("\n[4/4] Case1 API統合テスト（約1分）...")
    try:
        import pytest  # noqa: F401
    except ImportError:
        print("  NG: pytest がインストールされていません。以下を実行してください:")
        print("     cd Dev/backend && pip install -r requirements_test.txt")
        print("     または: pip install pytest requests")
        return 1

    backend_dir = Path(__file__).resolve().parent.parent / "backend"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/integration/test_case1_demo_flow.py", "-v", "--tb=short"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode == 0:
        print("  OK: Case1フロー統合テスト成功")
    else:
        print("  NG: 統合テスト失敗")
        print(result.stdout)
        print(result.stderr)
        return 1

    print("\n=== 全検証完了: デプロイ可能 ===")
    print("ブラウザで http://localhost:3000/demo/case1 を開き、手動でフローを確認してください。\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
