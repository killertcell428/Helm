# ポート 8000 を使用しているプロセスを強制終了する（uvicorn が Ctrl+C で止まらないとき用）
# 使い方: .\scripts\kill_port_8000.ps1  または  powershell -File scripts\kill_port_8000.ps1

$port = 8000
$found = $false

Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object {
    $pid = $_.OwningProcess
    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
    Write-Host "Port $port is used by PID $pid ($($proc.ProcessName)). Killing..."
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    $found = $true
}

if (-not $found) {
    Write-Host "No process found listening on port $port."
} else {
    Write-Host "Done. Port $port should be free now."
}
