# サーバー・テストの止め方（Windows）

## バックエンド（uvicorn）が Ctrl+C で止まらないとき

### 1. もう一度 Ctrl+C
- **1回目**: 終了要求（Graceful shutdown）
- **2回目**: 強制終了
- 2回連続で押してみる。

### 2. ターミナルを閉じる
- Cursor のターミナルなら、タブのゴミ箱アイコンでタブを閉じる。
- そのターミナルで動いていたプロセスは終了する。

### 3. プロセスを手動で終了する（PowerShell）

**ポート 8000 を使っているプロセスを確認:**
```powershell
netstat -ano | findstr :8000
```
右端の数字が **PID**。例: `12345`

**その PID を終了:**
```powershell
taskkill /PID 12345 /F
```
（`12345` を実際の PID に置き換える）

**または「ポート 8000 を使っているプロセス」を一発で終了:**
```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

**リポジトリ内のスクリプトを使う場合（backend フォルダで実行）:**
```powershell
cd Dev\backend
.\scripts\kill_port_8000.ps1
```

---

## pytest の止め方

### 1. Ctrl+C を 2 回
- **1回目**: 現在のテスト終了後に終了（完了を待つ）
- **2回目**: すぐに強制終了
- 固まっているときは **Ctrl+C を 2 回** 押す。

### 2. 長時間テストを避けたいとき
- パフォーマンステストだけスキップして実行:
  ```powershell
  pytest tests/unit tests/integration -v -m "not slow"
  ```
- 1 つ失敗したらそこで止める:
  ```powershell
  pytest tests/unit tests/integration -v -x
  ```

### 3. pytest のプロセスを強制終了（PowerShell）
```powershell
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq '' } | Stop-Process -Force
```
（他の Python プロセスも止まるので、他に Python を動かしていないときだけ使う）

**特定の PID だけ止める場合:**
1. タスクマネージャーで「python」を探して PID を確認して終了する。
2. または `tasklist | findstr python` で PID を確認し、`taskkill /PID ＜PID＞ /F` で終了。

---

## まとめ

| やりたいこと           | 操作 |
|------------------------|------|
| uvicorn を止める       | Ctrl+C を 2 回 → ダメならターミナルを閉じる or 上記 `taskkill` |
| pytest を止める        | Ctrl+C を 2 回 |
| ポート 8000 を空ける   | `Get-NetTCPConnection -LocalPort 8000 ... \| ... Stop-Process` を実行 |
