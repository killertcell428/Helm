# ドキュメントインデックス

Helmプロジェクトの主要ドキュメント一覧です。

## 📖 メインドキュメント

### プロジェクト概要
- [README.md](./README.md) - プロジェクトの概要とクイックスタート
- [docs/guides/QUICKSTART.md](./docs/guides/QUICKSTART.md) - 初心者向け起動手順
- [ARCHITECTURE.md](./ARCHITECTURE.md) - システム全体の設計

### 進捗・実装状況
- [docs/status/DEVELOPMENT_STATUS_SUMMARY.md](./docs/status/DEVELOPMENT_STATUS_SUMMARY.md) - **現状の開発状況**と**ネクストステップ**の整理 ⭐ **最新**
- [docs/status/CURRENT_DEVELOPMENT_STATUS.md](./docs/status/CURRENT_DEVELOPMENT_STATUS.md) - 開発状況の詳細
- [docs/status/NEXT_STEPS.md](./docs/status/NEXT_STEPS.md) - 次のステップ（タスク単位・完了済み含む）
- [docs/status/PROJECT_STATUS.md](./docs/status/PROJECT_STATUS.md) - プロジェクト状況
- [docs/status/WEEK2_SUMMARY.md](./docs/status/WEEK2_SUMMARY.md) - Week 2の実装サマリー
- [docs/status/CLEANUP_SUMMARY.md](./docs/status/CLEANUP_SUMMARY.md) - ファイル整理サマリー

### 実装詳細
- [backend/REAL_DATA_IMPLEMENTATION.md](./backend/REAL_DATA_IMPLEMENTATION.md) - 実データ実装の詳細
- [backend/API_DOCUMENTATION.md](./backend/API_DOCUMENTATION.md) - API仕様書

### 設計・運用（ガバナンスまわり）
- [docs/auth-api-key-roles.md](./docs/auth-api-key-roles.md) - 認証（API Key ＋ ロール）設計・有効化方法
- [docs/data-retention.md](./docs/data-retention.md) - データ保存期間と自動削除の設計
- [docs/idempotency-execute.md](./docs/idempotency-execute.md) - 冪等性（execute）の設計
- [docs/future/](./docs/future/) - 将来実装の設計（オーナーシップ、マルチテナント、ジョブキュー、通知ポリシー）

## 🔧 セットアップガイド

### 開発者向けガイド
- [docs/guides/DEVELOPER_GUIDE.md](./docs/guides/DEVELOPER_GUIDE.md) - 開発者向けガイド
- [docs/guides/USER_GUIDE.md](./docs/guides/USER_GUIDE.md) - ユーザーガイド
- [docs/guides/GIT_SETUP_GUIDE.md](./docs/guides/GIT_SETUP_GUIDE.md) - Gitセットアップガイド

### Google API統合
- [backend/QUICK_SETUP_PERSONAL_DRIVE.md](./backend/QUICK_SETUP_PERSONAL_DRIVE.md) - 個人アカウントでのセットアップ（推奨）
- [backend/SETUP_PERSONAL_DRIVE.md](./backend/SETUP_PERSONAL_DRIVE.md) - 個人アカウントでの詳細セットアップ
- [backend/SETUP_SHARED_DRIVE.md](./backend/SETUP_SHARED_DRIVE.md) - Google Workspace（共有ドライブ）でのセットアップ
- [backend/VERTEX_AI_SETUP.md](./backend/VERTEX_AI_SETUP.md) - Vertex AI設定ガイド

### バックエンド
- [backend/README.md](./backend/README.md) - バックエンドの概要
- [backend/SETUP.md](./backend/SETUP.md) - バックエンドの詳細セットアップ

## 📐 アーキテクチャ設計

- [Architectures/](./Architectures/) - アーキテクチャ設計資料
  - `Helm_3cases_PDCA.md` - 3ケースのPDCAサイクル
  - `Helm_final_3months_roles.md` - 3ヶ月後のロール設計
  - `Helm_parsers_3cases.md` - 3ケースのパーサー設計

## 📊 レポート・テスト結果

### テストレポート
- [docs/reports/BROWSER_TEST_REPORT_LLM_INTEGRATION.md](./docs/reports/BROWSER_TEST_REPORT_LLM_INTEGRATION.md) - LLM統合テストレポート
- [docs/reports/BROWSER_TEST_REPORT_LLM_TRUE.md](./docs/reports/BROWSER_TEST_REPORT_LLM_TRUE.md) - LLM実装テストレポート
- [docs/reports/BROWSER_TEST_REPORT_UI_UX.md](./docs/reports/BROWSER_TEST_REPORT_UI_UX.md) - UI/UXテストレポート
- [docs/reports/TEST_AND_ERROR_HANDLING_SUMMARY.md](./docs/reports/TEST_AND_ERROR_HANDLING_SUMMARY.md) - テストとエラーハンドリングサマリー

### LLM関連レポート
- [docs/reports/LLM_DEBUG_REPORT.md](./docs/reports/LLM_DEBUG_REPORT.md) - LLMデバッグレポート
- [docs/reports/LLM_STATUS_FINAL_REPORT.md](./docs/reports/LLM_STATUS_FINAL_REPORT.md) - LLMステータス最終レポート
- [docs/reports/LLM_VERIFICATION_REPORT.md](./docs/reports/LLM_VERIFICATION_REPORT.md) - LLM検証レポート

### LLM関連ドキュメント
- [docs/LLM_MOCK_VS_REAL.md](./docs/LLM_MOCK_VS_REAL.md) - モックと実装の比較
- [docs/LLM_PROBLEM_RESOLVED.md](./docs/LLM_PROBLEM_RESOLVED.md) - LLM問題解決記録
- [docs/LLM_PROBLEM_SOLUTION.md](./docs/LLM_PROBLEM_SOLUTION.md) - LLM問題解決方法

## 🗂️ アーカイブ

開発過程で作成された中間生成物は [archive/](./archive/) フォルダに保存されています。

- [archive/README.md](./archive/README.md) - アーカイブフォルダの説明
- ユーザー作業ガイド（実装完了後）
- テストスクリプト（開発用）
- 実装計画書（完了後）
- 動作確認レポート（完了後）

## 📝 開発資料

- [dev_docs/](./dev_docs/) - 開発用資料
  - `Data/` - データ分析資料
  - `Demo/` - デモスクリプト
  - `Scripts/` - トーク原稿
  - `Summary/` - サマリー資料
  - `Technical/` - 技術資料
  - `Vision/` - ビジョン資料

※ 内部用ドキュメント（上司フィードバック・戦略メモ・旧版アーカイブなど）はリポジトリに含みません。

## 🔍 ドキュメントの探し方

### セットアップ関連
- クイックスタート: [docs/guides/QUICKSTART.md](./docs/guides/QUICKSTART.md)
- 個人アカウント: [backend/QUICK_SETUP_PERSONAL_DRIVE.md](./backend/QUICK_SETUP_PERSONAL_DRIVE.md)
- Google Workspace: [backend/SETUP_SHARED_DRIVE.md](./backend/SETUP_SHARED_DRIVE.md)
- Vertex AI: [backend/VERTEX_AI_SETUP.md](./backend/VERTEX_AI_SETUP.md)

### 実装状況
- 最新の実装サマリー: [docs/status/WEEK2_SUMMARY.md](./docs/status/WEEK2_SUMMARY.md)
- 詳細な進捗: [docs/status/WEEK2_PROGRESS.md](./docs/status/WEEK2_PROGRESS.md)
- 次のステップ: [docs/status/NEXT_STEPS.md](./docs/status/NEXT_STEPS.md)
- プロジェクト状況: [docs/status/PROJECT_STATUS.md](./docs/status/PROJECT_STATUS.md)

### API仕様・認証
- [backend/API_DOCUMENTATION.md](./backend/API_DOCUMENTATION.md)
- [docs/auth-api-key-roles.md](./docs/auth-api-key-roles.md) - API Key 認証の有効化
- Swagger UI: http://localhost:8000/docs（サーバー起動時）

### トラブルシューティング
- [backend/TROUBLESHOOTING.md](./backend/TROUBLESHOOTING.md)
