$ErrorActionPreference = 'Stop'

param(
    [int]$Port = 0
)

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Warning "[WARN] $msg" }
function Write-Err($msg) { Write-Error "[ERROR] $msg" }

# Resolve port: prefer explicit param, then env var, default 3000
if (-not $Port -or $Port -le 0) {
    if ($env:PORT) { $Port = [int]$env:PORT } else { $Port = 3000 }
}

Write-Info "Using PORT=$Port"

Write-Info 'Checking Node.js and npm versions...'
try {
    $nodeVer = (node -v)
    $npmVer = (npm -v)
    Write-Info "Node: $nodeVer, npm: $npmVer"
} catch {
    Write-Err 'Node.js or npm not found. Please install Node.js 14+ and npm 6+.'
    exit 1
}

Write-Info 'Installing dependencies (npm install)...'
try {
    npm install
} catch {
    Write-Err "npm install failed: $($_.Exception.Message)"
    exit 1
}

Write-Info "Checking if port $Port is in use..."
$portInUse = $false
try {
    $netstat = netstat -ano | Select-String ":$Port\s"
    if ($netstat) {
        $portInUse = $true
        Write-Warn "Port $Port appears to be in use. Details:"
        $netstat | ForEach-Object { $_.Line }
    }
} catch {
    Write-Warn 'Port check encountered an issue, continuing.'
}

if ($portInUse) {
    Write-Err "Please free port $Port or run: .\\start.ps1 -Port <another_port>"
    exit 1
}

$env:PORT = "$Port"
Write-Info "Starting server with: node index.js"
Write-Host "Preview URL: http://localhost:$Port/" -ForegroundColor Green
node index.js