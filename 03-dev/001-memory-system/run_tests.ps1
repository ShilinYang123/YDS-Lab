Param(
  [switch]$IncludeNode
)

Write-Host "[Dev] Running Memory System tests..." -ForegroundColor Cyan

# 当前脚本目录：S:\YDS-Lab\03-dev\001-memory-system
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition

# 运行 Python 测试
Write-Host "[Python] Running test_intelligent_monitor.py" -ForegroundColor Yellow
python "$scriptRoot\tests\test_intelligent_monitor.py"
if ($LASTEXITCODE -ne 0) { Write-Error "test_intelligent_monitor.py failed"; exit $LASTEXITCODE }

Write-Host "[Python] Running test_longmemory_integration.py" -ForegroundColor Yellow
python "$scriptRoot\tests\test_longmemory_integration.py"
if ($LASTEXITCODE -ne 0) { Write-Error "test_longmemory_integration.py failed"; exit $LASTEXITCODE }

# 可选：运行 TraeLM 的 Node 测试
if ($IncludeNode) {
  $traeDir = Join-Path $scriptRoot "TraeLM"
  if (Test-Path (Join-Path $traeDir "package.json")) {
    Write-Host "[Node] Running TraeLM tests" -ForegroundColor Yellow
    Push-Location $traeDir
    npm install
    if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Error "npm install failed"; exit $LASTEXITCODE }
    npm test
    $exitCode = $LASTEXITCODE
    Pop-Location
    if ($exitCode -ne 0) { Write-Error "npm test failed"; exit $exitCode }
  } else {
    Write-Warning "TraeLM/package.json not found. Skipping Node tests."
  }
}

Write-Host "All dev tests completed successfully." -ForegroundColor Green