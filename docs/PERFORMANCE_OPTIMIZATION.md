# パフォーマンス最適化

開発・テストで実施したパフォーマンス最適化の概要です。

## バックエンド

### API レスポンスキャッシュ

- **対象**
  - `GET /` … ヘルスチェック。`Cache-Control: public, max-age=5` を付与（クライアント・CDN キャッシュ用）。
  - `GET /api/analysis/{analysis_id}` … 分析結果をメモリに TTL キャッシュ（同一 ID の再取得を軽量化）。
  - `GET /api/execution/{execution_id}/results` … 完了済み実行結果をメモリに TTL キャッシュ。
- **実装**: `backend/utils/simple_cache.py`（スレッドセーフな TTL キャッシュ）。
- **環境変数**
  - `CACHE_ANALYSIS_TTL_SECONDS` … 分析キャッシュ TTL（デフォルト 300 秒）。
  - `CACHE_RESULTS_TTL_SECONDS` … 実行結果キャッシュ TTL（デフォルト 300 秒）。
- **注意**: 単一プロセス・インメモリのため、Cloud Run で複数インスタンスがある場合はインスタンスごとのキャッシュです。

## フロントエンド

### 画像最適化

- **next.config.mjs**: `images.unoptimized` を `false` に変更。`next/image` 利用時に Next.js（および Vercel）の画像最適化が有効になります。

### コード分割（遅延読み込み）

- **app/demo/page.tsx**: ダッシュボード用コンポーネント（`SegmentTable`, `RevenueChart`, `BusinessUnitCards`）を `next/dynamic` で遅延読み込み。recharts を含むチャートを別チャンクに分離し、初期 JS サイズを削減しています。

## パフォーマンステスト

- **backend/tests/perf/test_api_latency.py**
  - `test_api_latency_root` … `GET /` のレイテンシ計測。
  - `test_api_latency_get_analysis_cache_hit` … 同一 `analysis_id` で 1 回目と 2 回目以降の応答時間を比較し、キャッシュヒット時が同等または高速であることを確認。
- 実行: バックエンド起動後に `pytest tests/perf -v -m slow` で実行。

## 今後の拡張候補

- API レスポンスのキャッシュ: 分散キャッシュ（Redis 等）の導入（マルチインスタンス時）。
- フロント: ルート単位のさらに細かいコード分割、`next/image` の活用拡大。
- CDN / Cache-Control: 静的アセットや GET のキャッシュポリシー見直し。
