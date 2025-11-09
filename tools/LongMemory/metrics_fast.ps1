param(
  [int]$IntervalSec = 30,
  [string]$TraeLMPidFile = "S:\YDS-Lab\03-dev\001-memory-system\TraeLM\traelm.pid",
  [int]$Port = 8765,
  [string]$TestHost = "localhost"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$healthScript = Join-Path $scriptDir 'health_check.ps1'

Write-Output "[metrics_fast] starting 30s metrics loop..."
while ($true) {
  try {
    & $healthScript -MetricsOnly -TraeLMPidFile $TraeLMPidFile -Port $Port -TestHost $TestHost | Out-Null
  } catch {
    Write-Warning "[metrics_fast] error: $($_.Exception.Message)"
  }
  Start-Sleep -Seconds $IntervalSec
}