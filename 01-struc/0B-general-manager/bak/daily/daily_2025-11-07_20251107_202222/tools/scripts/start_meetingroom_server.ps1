Param(
  [string]$Host = '127.0.0.1',
  [int]$Port = 8020
)

$repoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
Set-Location $repoRoot
Write-Host "Launching JS001 Meetingroom server at http://$Host:$Port/" -ForegroundColor Cyan
python 03-dev/JS001-meetingroom/servers/meetingroom_server.py --host $Host --port $Port