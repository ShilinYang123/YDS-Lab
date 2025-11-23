# Manual Interactive MTU and Heartbeat Parameter Test Script
# Author: Yu Jun (Technical Lead)
# Purpose: Manually test different MTU and heartbeat value combinations for network performance

param(
    [string]$LogFile = "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\manual_test_results.log"
)

# MTU and PersistentKeepalive test combinations (starting from 1450, descending)
$testCombinations = @(
    @{MTU=1450; Keepalive=25},
    @{MTU=1450; Keepalive=30},
    @{MTU=1450; Keepalive=60},
    @{MTU=1420; Keepalive=25},
    @{MTU=1420; Keepalive=30},
    @{MTU=1420; Keepalive=60},
    @{MTU=1400; Keepalive=25},
    @{MTU=1400; Keepalive=30},
    @{MTU=1400; Keepalive=60},
    @{MTU=1350; Keepalive=25},
    @{MTU=1350; Keepalive=30},
    @{MTU=1350; Keepalive=60},
    @{MTU=1280; Keepalive=25},
    @{MTU=1280; Keepalive=30},
    @{MTU=1280; Keepalive=60},
    @{MTU=1200; Keepalive=25},
    @{MTU=1200; Keepalive=30},
    @{MTU=1200; Keepalive=60}
)

# Test websites list
$TestSites = @(
    @{Name="Google"; URL="https://www.google.com"; IP="8.8.8.8"},
    @{Name="HuggingFace"; URL="https://huggingface.co"; IP="18.154.249.16"},
    @{Name="GitHub"; URL="https://github.com"; IP="140.82.112.3"}
)

function Initialize-Log {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $header = "=== Manual MTU and Heartbeat Parameter Test Started ===`nTime: $timestamp`nTest Description: Manual WireGuard config modification followed by website connectivity test`n"
    $header | Out-File -FilePath $LogFile -Encoding UTF8
    Write-Host $header -ForegroundColor Cyan
}

function Test-WebsiteConnectivity {
    param($Site)
    
    Write-Host "Testing $($Site.Name) ($($Site.URL))..." -ForegroundColor Yellow
    
    # Enhanced ping test with packet loss detection
    $pingSuccess = $false
    $packetLoss = 100
    $avgPingTime = 0
    
    try {
        $pingResults = Test-Connection -ComputerName $Site.IP -Count 10 -ErrorAction SilentlyContinue
        if ($pingResults) {
            $successfulPings = $pingResults | Where-Object { $_.StatusCode -eq 0 }
            $successCount = ($successfulPings | Measure-Object).Count
            $totalCount = ($pingResults | Measure-Object).Count
            
            if ($successCount -gt 0) {
                $pingSuccess = $true
                $packetLoss = [math]::Round((($totalCount - $successCount) / $totalCount) * 100, 1)
                $avgPingTime = [math]::Round(($successfulPings | Measure-Object -Property ResponseTime -Average).Average, 1)
            }
        }
    }
    catch {
        $pingSuccess = $false
        $packetLoss = 100
        $avgPingTime = 0
    }
    
    # HTTP connection test
    $httpResult = $false
    $responseTime = 0
    
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri $Site.URL -TimeoutSec 10 -UseBasicParsing
        $stopwatch.Stop()
        $responseTime = $stopwatch.ElapsedMilliseconds
        if ($response.StatusCode -eq 200) {
            $httpResult = $true
        }
    }
    catch {
        $httpResult = $false
        $responseTime = -1
    }
    
    $result = @{
        Name = $Site.Name
        URL = $Site.URL
        IP = $Site.IP
        PingSuccess = $pingSuccess
        PacketLoss = $packetLoss
        AvgPingTime = $avgPingTime
        HttpSuccess = $httpResult
        ResponseTime = $responseTime
    }
    
    return $result
}

function Run-WebsiteTests {
    $results = @()
    
    Write-Host "`nStarting website connectivity tests..." -ForegroundColor Green
    
    foreach ($site in $TestSites) {
        $result = Test-WebsiteConnectivity -Site $site
        $results += $result
        
        # Display test results with packet loss information
        $pingStatus = if ($result.PingSuccess) { "OK" } else { "FAIL" }
        $httpStatus = if ($result.HttpSuccess) { "OK" } else { "FAIL" }
        $timeDisplay = if ($result.ResponseTime -gt 0) { "$($result.ResponseTime)ms" } else { "Timeout" }
        $packetLossDisplay = "$($result.PacketLoss)%"
        $avgPingDisplay = if ($result.AvgPingTime -gt 0) { "$($result.AvgPingTime)ms" } else { "N/A" }
        
        Write-Host "  $($result.Name): Ping[$pingStatus] Loss[$packetLossDisplay] AvgPing[$avgPingDisplay] HTTP[$httpStatus] Response[$timeDisplay]" -ForegroundColor White
    }
    
    return $results
}

function Log-TestResults {
    param($MTU, $Keepalive, $Results)
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "`n[$timestamp] MTU=$MTU, Keepalive=$Keepalive`n"
    
    foreach ($result in $Results) {
        $pingStatus = if ($result.PingSuccess) { "Success" } else { "Failed" }
        $httpStatus = if ($result.HttpSuccess) { "Success" } else { "Failed" }
        $timeDisplay = if ($result.ResponseTime -gt 0) { "$($result.ResponseTime)ms" } else { "Timeout" }
        $packetLossDisplay = "$($result.PacketLoss)%"
        $avgPingDisplay = if ($result.AvgPingTime -gt 0) { "$($result.AvgPingTime)ms" } else { "N/A" }
        
        $logEntry += "  $($result.Name): Ping[$pingStatus] Loss[$packetLossDisplay] AvgPing[$avgPingDisplay] HTTP[$httpStatus] Response[$timeDisplay]`n"
    }
    
    $logEntry | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

function Show-ParameterPrompt {
    param($MTU, $Keepalive)
    
    Write-Host "`n" -ForegroundColor White
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Please manually modify the following parameters in WireGuard config:" -ForegroundColor Yellow
    Write-Host "MTU = $MTU" -ForegroundColor Green
    Write-Host "PersistentKeepalive = $Keepalive" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Please modify MTU and PersistentKeepalive in WireGuard GUI (PC3.conf)" -ForegroundColor White
    Write-Host "After modification, please reconnect VPN, then press any key to continue testing..." -ForegroundColor Yellow
    Write-Host "==========================================" -ForegroundColor Cyan
}

function Wait-UserConfirmation {
    Read-Host "Press Enter to continue testing"
}

function Show-TestSummary {
    param($AllResults)
    
    Write-Host "`n" -ForegroundColor White
    Write-Host "=== Test Summary ===" -ForegroundColor Cyan
    Write-Host "Completed all $($AllResults.Count) parameter combination tests" -ForegroundColor Green
    Write-Host "Detailed results can be found in log file: $LogFile" -ForegroundColor White
    
    # Find configuration with highest success rate
    $bestConfig = $null
    $bestSuccessRate = -1
    
    foreach ($result in $AllResults) {
        $successCount = 0
        $totalTests = $result.Results.Count * 2  # Ping + HTTP
        
        foreach ($siteResult in $result.Results) {
            if ($siteResult.PingSuccess) { $successCount++ }
            if ($siteResult.HttpSuccess) { $successCount++ }
        }
        
        $successRate = $successCount / $totalTests
        
        if ($successRate -gt $bestSuccessRate) {
            $bestSuccessRate = $successRate
            $bestConfig = $result
        }
    }
    
    if ($bestConfig) {
        Write-Host "`nRecommended configuration (highest success rate):" -ForegroundColor Yellow
        Write-Host "MTU = $($bestConfig.MTU)" -ForegroundColor Green
        Write-Host "PersistentKeepalive = $($bestConfig.Keepalive)" -ForegroundColor Green
        Write-Host "Success rate: $([math]::Round($bestSuccessRate * 100, 1))%" -ForegroundColor Green
    }
    
    Write-Host "`nTest completed!" -ForegroundColor Cyan
}

function Start-ManualTest {
    Initialize-Log
    
    Write-Host "Manual MTU and Heartbeat Parameter Test Script Started" -ForegroundColor Green
    Write-Host "Total $($TestCombinations.Count) parameter combinations to test" -ForegroundColor White
    Write-Host "Each test will check connectivity to Google, HuggingFace, GitHub`n" -ForegroundColor White
    
    $testNumber = 1
    $allResults = @()
    
    foreach ($combination in $TestCombinations) {
        Write-Host "`n=== Test $testNumber/$($TestCombinations.Count) ===" -ForegroundColor Magenta
        
        # Show parameter modification prompt
        Show-ParameterPrompt -MTU $combination.MTU -Keepalive $combination.Keepalive
        
        # Wait for user to manually modify config and connect VPN
        Wait-UserConfirmation
        
        # Execute website tests
        $testResults = Run-WebsiteTests
        
        # Log results
        Log-TestResults -MTU $combination.MTU -Keepalive $combination.Keepalive -Results $testResults
        
        # Save to summary results
        $resultItem = @{
            MTU = $combination.MTU
            Keepalive = $combination.Keepalive
            Results = $testResults
            TestNumber = $testNumber
        }
        $allResults += $resultItem
        
        $testNumber++
        
        Write-Host "`nTest completed, results logged to file" -ForegroundColor Green
        
        if ($testNumber -le $TestCombinations.Count) {
            Write-Host "Preparing for next test..." -ForegroundColor White
        }
    }
    
    # Show test summary
    Show-TestSummary -AllResults $allResults
}

# Start test
Start-ManualTest