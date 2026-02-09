# アーカイブフォルダ

このフォルダには、開発過程で作成された中間生成物や一時的なドキュメントが保存されています。

## フォルダ構成

```
archive/
├── backend/
│   ├── USER_TASKS_STEP*.md          # ユーザー作業ガイド（実装完了後）
│   ├── test_google_*.py              # 実APIテストスクリプト（開発用）
│   ├── REAL_API_IMPLEMENTATION_PLAN.md  # 実装計画書（完了後）
│   ├── IMPLEMENTATION_STATUS.md      # 実装状況追跡（完了後）
│   └── TEST_*.md                     # テスト関連ドキュメント（完了後）
└── BROWSER_TEST_REPORT*.md           # 動作確認レポート（完了後）
```

## ファイル説明

### ユーザー作業ガイド
- `USER_TASKS_STEP1_DRIVE.md`: Google Drive API設定ガイド
- `USER_TASKS_STEP2_DOCS.md`: Google Docs API設定ガイド
- `USER_TASKS_STEP3_CHAT.md`: Google Chat API設定ガイド
- `USER_TASKS_STEP4_MEET.md`: Google Meet API設定ガイド

**用途**: 実装時のユーザー作業手順書。実装完了後は参考資料としてアーカイブ。

### テストスクリプト
- `test_google_drive_real.py`: Google Drive API実装テスト
- `test_google_docs_real.py`: Google Docs API実装テスト
- `test_google_chat_real.py`: Google Chat API実装テスト
- `test_google_meet_real.py`: Google Meet API実装テスト
- `test_mock_services.py`: モックサービステスト

**用途**: 実API統合時の動作確認用スクリプト。実装完了後は参考資料としてアーカイブ。

### 実装計画・状況
- `REAL_API_IMPLEMENTATION_PLAN.md`: 実API実装の段階的計画
- `IMPLEMENTATION_STATUS.md`: 各ステップの実装状況追跡

**用途**: 実装進行中の計画・追跡ドキュメント。実装完了後は参考資料としてアーカイブ。

### 動作確認レポート
- `BROWSER_TEST_REPORT.md`: 初期動作確認レポート
- `BROWSER_TEST_REPORT_FINAL.md`: 構文エラー修正後の動作確認レポート
- `BROWSER_TEST_REPORT_COMPLETE.md`: 全機能動作確認レポート

**用途**: ブラウザでの動作確認結果記録。確認完了後は参考資料としてアーカイブ。

## 注意事項

- これらのファイルは削除せず、アーカイブとして保存しています
- 必要に応じて参照できますが、最新の情報はメインのドキュメントを参照してください
- メインのドキュメント:
  - `WEEK2_SUMMARY.md` - Week 2の実装サマリー
  - `WEEK2_PROGRESS.md` - 詳細な進捗記録
  - `backend/REAL_DATA_IMPLEMENTATION.md` - 実データ実装の詳細
