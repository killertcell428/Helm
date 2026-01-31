gcloud run services update reacha-app `
  --region asia-northeast1 `
  --update-env-vars `
    DIFY_API_KEY1=app-BfDFjZRyj3qBakTTxVZNOt1J,`
    DIFY_API_KEY2=app-dI8MOoihsJo04pNh2fzfehtd,`
    DIFY_USER_ID=REACHA_agent


DIFY_API_KEY1=app-BfDFjZRyj3qBakTTxVZNOt1J  # 既存のキー
DIFY_API_KEY2=app-dI8MOoihsJo04pNh2fzfehtd  # ワークフローAPI用のキーを設定
DIFY_API_KEY3=app-5tLzX7Dgjfn05yLqyGKeeyeh  # キーワード抽出のキー
DIFY_USER_ID=REACHA_agent
DIFY_TIMEOUT=10800
DIFY_MAX_RETRIES=3
DIFY_RETRY_BACKOFF_SECONDS=10
DIFY_INTER_QUERY_DELAY_SECONDS=8