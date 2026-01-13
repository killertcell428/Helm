#!/usr/bin/env python3
"""環境変数の確認スクリプト"""
import os
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

print("=== 環境変数の確認 ===")
print(f"USE_LLM: {os.getenv('USE_LLM')}")
print(f"GOOGLE_CLOUD_PROJECT_ID: {os.getenv('GOOGLE_CLOUD_PROJECT_ID')}")
print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

print("\n=== 依存関係の確認 ===")
try:
    from google.cloud import aiplatform
    print("google-cloud-aiplatform: ✅ インストール済み")
except ImportError as e:
    print(f"google-cloud-aiplatform: ❌ 未インストール - {e}")

print("\n=== LLM統合の状態 ===")
use_llm = os.getenv("USE_LLM", "false").lower() == "true"
project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")

if not use_llm:
    print("❌ USE_LLM=false のため、LLM統合は無効")
elif not project_id:
    print("❌ GOOGLE_CLOUD_PROJECT_ID未設定のため、LLM統合は無効")
else:
    print(f"✅ USE_LLM=true, GOOGLE_CLOUD_PROJECT_ID={project_id}")
    try:
        from google.cloud import aiplatform
        print("✅ Vertex AI利用可能")
    except ImportError:
        print("❌ google-cloud-aiplatformがインストールされていません")
    except Exception as e:
        print(f"❌ Vertex AI初期化エラー: {e}")
