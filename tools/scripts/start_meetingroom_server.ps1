Param(
  [string]$ConfigPath = "S:\YDS-Lab\config\meetingroom_config.json"
)

$repoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
Set-Location $repoRoot

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
}

chcp 65001 | Out-Null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
if ($jwtRequired -eq 'True' -or $jwtRequired -eq 'true') {
  $env:WS_JWT_REQUIRED = 'true'
} else {
  $env:WS_JWT_REQUIRED = 'false'
}

$previewUrl = "http://$($host):$($port)/"
Write-Host "Launching 002 Meetingroom server at $previewUrl (WS_JWT_REQUIRED=$($env:WS_JWT_REQUIRED))" -ForegroundColor Cyan
python 03-dev/002-meetingroom/servers/meetingroom_server.py --host $host --port $port