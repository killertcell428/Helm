# 認証（API Key ＋ ロール）設計

## 概要

API へのアクセスを API Key で認証し、キーに紐づくロールで認可（どのエンドポイントを叩けるか）を制御する。実装済み（`main.py` の `APIKeyAuthMiddleware`、`config.API_KEYS`）。

## 有効化方法

- **オフ（デフォルト）**: 環境変数 `API_KEYS` を設定しない、または空の配列 `[]` のとき。このときは **キー不要** で全リクエストを通し、`X-User-Role` / `X-User-ID` があれば監査用に使い、なければ `system` とする。
- **オン**: 環境変数 `API_KEYS` に JSON 配列を設定する。例（PowerShell）:
  - `$env:API_KEYS='[{"key":"your-secret-key","role":"operator"}]'`
  - または **オーナー用キー1本**で有効にする: `.env` に次の1行を追加（backend 直下の `.env`、UTF-8 で保存）。
    ```env
    API_KEYS=[{"key":"helm-owner-dev-key","role":"owner"}]
    ```
  - 参考: `backend/.env.example` に同じ形式のサンプルあり。本番ではキーを必ず変更すること。
- オンにすると、`/`・`/docs`・`/redoc`・`/openapi.json` 以外のパスで **`X-API-Key` 必須**。無いと 401、不正なキーだと 403。キーが有効なら `request.state.role` / `request.state.user_id` が監査ログに使われる。

## 認証方式

- **ヘッダ**: `X-API-Key: <key>` で API Key を送信。
- **ロールの扱い**: API Key に 1 ロールを紐付ける。検証後に `X-User-Role` をリクエストコンテキストに設定し、既存の監査ログ・承認フローで利用する。
- **ユーザー識別**: オプションで `X-User-ID` をクライアントが送る。未設定時は API Key の識別子を user_id として使う。

## キーとロールの管理

- **保存**: 初期は環境変数または設定ファイルで `API_KEYS` を JSON 配列（例: `[{"key":"xxx","role":"viewer"},{"key":"yyy","role":"admin"}]`）で持つ。本番では Secret Manager や DB を推奨。
- **ロール例**: `viewer`（参照のみ）, `operator`（ingest/analyze/escalate/approve/execute）, `admin`（管理 API 含む）。

## 検証フロー

1. リクエストから `X-API-Key` を取得。
2. キーが有効か照合。一致したら紐づくロールを取得。
3. ルートごとに必要ロールを定義（例: `/api/admin/*` は `admin` のみ）。不足なら 403。
4. 検証通過後、`request.state.role` および必要なら `request.state.user_id` を設定。監査ログの `role` / `user_id` はここから取得。

## 除外パス

- ヘルスチェック `/`、ドキュメント `/docs` 等は認証不要とする。
- `X-API-Key` が無い場合、認証必須ルートでは 401 を返す。

## 将来拡張

- OIDC / サービスアカウント連携。
- ロールのきめ細かい権限（パターン別・リソース別）。
