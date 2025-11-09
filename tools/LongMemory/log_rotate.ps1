function Invoke-LogRotate {
    param([string]$LogsDir)
    $bakDir = Join-Path $LogsDir "bak"
    if (!(Test-Path $bakDir)) { New-Item -ItemType Directory -Path $bakDir -Force | Out-Null }
    $limit = (Get-Date).AddDays(-30)
    Get-ChildItem -Path $LogsDir -Filter "health_*.jsonl" |
        Where-Object { $_.LastWriteTime -lt $limit } |
        ForEach-Object {
            Move-Item -Path $_.FullName -Destination (Join-Path $bakDir $_.Name) -Force
        }
    Get-ChildItem -Path $bakDir -Filter "health_*.jsonl" |
        Where-Object { $_.LastWriteTime -lt $limit.AddDays(-30) } |
        Remove-Item -Force
}