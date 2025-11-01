Param(
  [string]$Host = '127.0.0.1',
  [int]$Port = 8020
)

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
Write-Host "Launching JS001 Meetingroom server at http://$Host:$Port/" -ForegroundColor Cyan
python tools/servers/meetingroom_server.py --host $Host --port $Port