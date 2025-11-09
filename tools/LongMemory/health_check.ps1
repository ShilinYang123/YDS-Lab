param(
    [string]$LogsRoot = "S:\YDS-Lab\01-struc\0B-general-manager\logs\longmemory",
    [string]$TraeLMPidFile = "",
    [int]$Port = 8765,
    [string]$TestHost = "localhost",
    [switch]$MetricsOnly
)
$ErrorActionPreference = "Stop"
. $PSScriptRoot\log_rotate.ps1
try {
    $healthDir = Join-Path $LogsRoot "health"
    if (!(Test-Path $healthDir)) { New-Item -ItemType Directory -Path $healthDir -Force | Out-Null }
    $dateStr = Get-Date -Format "yyyyMMdd"
    $timestamp = Get-Date -Format "o"
    $snapshotFile = Join-Path $healthDir ("health_" + $dateStr + ".jsonl")
    if (-not $MetricsOnly) { Invoke-LogRotate -LogsDir $healthDir }
    $pidInfo = @{ pid = $null; cpu = $null; mem = $null }
    if ($TraeLMPidFile -and (Test-Path $TraeLMPidFile)) {
        try {
            $pid = Get-Content $TraeLMPidFile -Raw | ConvertFrom-Json | Select-Object -ExpandProperty pid
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc) {
                $pidInfo.pid = $pid
                $pidInfo.cpu = [math]::Round($proc.CPU, 2)
                $pidInfo.mem = [math]::Round($proc.WorkingSet64 / 1MB, 2)
            }
        } catch {}
    }
    $portListening = $false
    try {
        $listener = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties()
        $tcpConn = $listener.GetActiveTcpListeners() | Where-Object { $_.Port -eq $Port }
        $portListening = ($tcpConn.Count -gt 0)
    } catch {}
    $pingOk = $false
    try { $pingOk = Test-Connection -ComputerName $TestHost -Count 1 -Quiet } catch {}
    $healthObj = $null
    try {
        $healthObj = Invoke-RestMethod -Uri "http://localhost:8765/health" -TimeoutSec 3
        $healthStatus = "online"
    } catch {
        $healthStatus = "offline"
        $healthObj = @{ error = $_.Exception.Message }
    }
    $pyOutput = ""; $pyExitCode = $null
    $pyScript = "S:\YDS-Lab\tools\LongMemory\health_check.py"
    if (Test-Path $pyScript) {
        try {
            $startInfo = New-Object System.Diagnostics.ProcessStartInfo
            $startInfo.FileName = "python"; $startInfo.Arguments = "`"$pyScript`""
            $startInfo.RedirectStandardOutput = $true; $startInfo.RedirectStandardError = $true; $startInfo.UseShellExecute = $false
            $process = New-Object System.Diagnostics.Process; $process.StartInfo = $startInfo
            $process.Start() | Out-Null
            $stdOut = $process.StandardOutput.ReadToEnd(); $stdErr = $process.StandardError.ReadToEnd()
            $process.WaitForExit(); $pyExitCode = $process.ExitCode
            $pyOutput = $(if ($stdErr) { ($stdOut + "`nERR: " + $stdErr).Trim() } else { $stdOut.Trim() })
        } catch {
            $pyOutput = "Failed to run health_check.py: " + $_.Exception.Message; $pyExitCode = -1
        }
    } else {
        $pyOutput = "health_check.py not found at $pyScript"; $pyExitCode = -2
    }
    $record = [PSCustomObject]@{
        timestamp = $timestamp
        service = "TraeLM"
        status = $healthStatus
        health = $healthObj
        metrics = @{ process = $pidInfo; portListening = $portListening; pingOk = $pingOk }
        python = @{ script = $pyScript; exitCode = $pyExitCode; output = $pyOutput }
    }
    # 生成紧凑的单行 JSON（去除换行），并确保每条记录以 CRLF 结尾，兼容 .jsonl 按行解析
    if (-not $MetricsOnly) {
        $json = $record | ConvertTo-Json -Depth 6
        $jsonLine = $json -replace '\r?\n',''
        Add-Content -Path $snapshotFile -Value ($jsonLine + "`r`n")
    }
    try {
        $memory = [PSCustomObject]@{
            content = "系统健康快照：$($record.status)"
            type = "long_term"
            importance = 5
            tags = @("health","ops","traelm")
            context = $json
            metadata = @{ source = "health_check.ps1"; version = "1.1" }
        }
        if (-not $MetricsOnly) {
            $storeBody = $memory | ConvertTo-Json -Depth 6
            $storeRes = Invoke-RestMethod -Uri "http://localhost:8765/store" -Method Post -Body $storeBody -ContentType "application/json" -TimeoutSec 5
            Write-Output "Health snapshot stored to TraeLM with id $($storeRes.id)"
        }
    } catch {
        Write-Warning "Failed to store health snapshot to TraeLM: $($_.Exception.Message)"
    }
    # 推送指标到 TraeLM /update-metrics
    try {
        $metric = @{
            cpu = $pidInfo.cpu
            mem = $pidInfo.mem
            portListening = $portListening
            pingOk = $pingOk
            pyExitCode = $pyExitCode
        }
        $metricBody = $metric | ConvertTo-Json
        Invoke-RestMethod -Uri "http://localhost:8765/update-metrics" -Method Post -Body $metricBody -ContentType "application/json" -TimeoutSec 3 | Out-Null
    } catch {
        Write-Warning "Failed to push metrics: $($_.Exception.Message)"
    }
    if (-not $MetricsOnly) { Write-Output "Health snapshot written to $snapshotFile at $timestamp" }
} catch {
    Write-Error "Health check failed: $($_.Exception.Message)"
    exit 1
}
