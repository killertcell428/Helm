"""Google Gen AI SDKでのテスト（新しいアプローチ）"""
import os

# Application Default Credentialsを優先
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    original_creds = os.environ.pop('GOOGLE_APPLICATION_CREDENTIALS')
    print(f"一時的にGOOGLE_APPLICATION_CREDENTIALSを無効化")

try:
    # Google Gen AI SDKを試す
    try:
        import google.generativeai as genai
        print("google.generativeai が利用可能です")
        
        # APIキーまたは認証情報を設定
        genai.configure()
        
        # モデルを取得
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("モデル初期化成功: gemini-1.5-flash")
        
        # テスト呼び出し
        response = model.generate_content("Hello")
        print(f"✅ SUCCESS: {response.text[:50]}")
        
    except ImportError:
        print("google.generativeai がインストールされていません")
        print("インストール: pip install google-generativeai")
        
        # 既存のVertex AI SDKを試す
        from google.cloud import aiplatform
        from vertexai.preview.generative_models import GenerativeModel
        
        project_id = "helm-project-484105"
        
        # コンソールで使用していたリージョンを確認する必要があります
        # 一般的なリージョンを試す
        for region in ["us-central1", "asia-northeast1"]:
            try:
                aiplatform.init(project=project_id, location=region)
                model = GenerativeModel("gemini-1.5-flash-002")
                response = model.generate_content("Hello")
                print(f"✅ SUCCESS (Vertex AI SDK): リージョン={region}, レスポンス={response.text[:50]}")
                break
            except Exception as e:
                print(f"リージョン {region}: エラー - {str(e)[:100]}")
                
except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'original_creds' in locals():
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = original_creds
