Param(
  [string]$ConfigPath = "S:\YDS-Lab\config\meetingroom_config.json"
)

$ErrorActionPreference = 'Stop'
try {
  if (-not (Test-Path $ConfigPath)) {
    throw "配置文件未找到: $ConfigPath"
  }
  $cfg = Get-Content -Raw -Path $ConfigPath | ConvertFrom-Json
  $host = $cfg.host
  $port = [int]$cfg.port
  $jwtRequired = [string]$cfg.ws_jwt_required
  if (-not $host) { $host = '127.0.0.1' }
  if (-not $port) { $port = 8020 }

  chcp 65001 | Out-Null
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

  if ($jwtRequired -eq 'True' -or $jwtRequired -eq 'true') {
    $env:WS_JWT_REQUIRED = 'true'
  } else {
    $env:WS_JWT_REQUIRED = 'false'
  }

  Write-Output "[PROD] Starting meetingroom server: host=$host port=$port WS_JWT_REQUIRED=$($env:WS_JWT_REQUIRED)"
  python "S:\YDS-Lab\03-dev\002-meetingroom\servers\meetingroom_server.py" --host $host --port $port
} catch {
  Write-Error "[PROD] 启动 meetingroom 失败: $($_.Exception.Message)"
  exit 1
}