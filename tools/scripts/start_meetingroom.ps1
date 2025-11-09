Param(
  [string]$ConfigPath = "S:\YDS-Lab\config\meetingroom_config.json"
)

if (-not (Test-Path $ConfigPath)) {
  Write-Warning "未找到配置文件: $ConfigPath，使用默认值"
  $host = '127.0.0.1'
  $port = 8020
  $jwtRequired = 'false'
} else {
  $cfg = Get-Content -Raw -Path $ConfigPath | ConvertFrom-Json
  $host = $cfg.host
  $port = [int]$cfg.port
  $jwtRequired = [string]$cfg.ws_jwt_required
  if (-not $host) { $host = '127.0.0.1' }
  if (-not $port) { $port = 8020 }
}

# 统一代码页
chcp 65001 | Out-Null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 设置 JWT 开关环境变量
if ($jwtRequired -eq 'True' -or $jwtRequired -eq 'true') {
  $env:WS_JWT_REQUIRED = 'true'
} else {
  $env:WS_JWT_REQUIRED = 'false'
}

Write-Output "Starting meetingroom server with host=$host port=$port WS_JWT_REQUIRED=$($env:WS_JWT_REQUIRED)"
python "S:\YDS-Lab\03-dev\002-meetingroom\servers\meetingroom_server.py" --host $host --port $port