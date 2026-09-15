# Build standalone executable from Node.js MCP agent
# Safe: uses parameter arrays, environment variables for paths

param(
    [string]$EntryPoint = "index.js",
    [string]$OutputDir = "dist",
    [int]$MaxSize = 35MB
)

$ErrorActionPreference = "Stop"

Write-Host "[PACKAGE] Building standalone agent..." -ForegroundColor Green

# Step 1: Validate entry point exists
if (-not (Test-Path $EntryPoint)) {
    Write-Host "[ERROR] Entry point not found: $EntryPoint" -ForegroundColor Red
    exit 1
}

# Step 2: Create output directory safely
if (Test-Path $OutputDir) {
    Remove-Item -Path $OutputDir -Recurse -Force
}
New-Item -ItemType Directory -Path $OutputDir | Out-Null

# Step 3: Use pkg to create standalone binary
# pkg is safer than PyInstaller for Node apps: no interpreter extraction needed
Write-Host "[PKG] Compiling agent to binary..." -ForegroundColor Cyan

$pkgArgs = @(
    $EntryPoint,
    "--output", (Join-Path $OutputDir "sentinel_agent.exe"),
    "--targets", "win-x64",
    "--compress", "Brotli"
)

& pkg @pkgArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pkg compilation failed" -ForegroundColor Red
    exit 1
}

# Step 4: Verify output size
$exePath = Join-Path $OutputDir "sentinel_agent.exe"
$size = (Get-Item $exePath).Length

if ($size -gt $MaxSize) {
    Write-Host "[WARN] Binary size ${size} exceeds limit ${MaxSize}" -ForegroundColor Yellow
} else {
    Write-Host "[OK] Binary size: $(${size}/1MB) MB" -ForegroundColor Green
}

Write-Host "[SUCCESS] Standalone agent built: $exePath" -ForegroundColor Green
Write-Host "[NEXT] Run installer.iss to create SentinelOps-Setup.exe" -ForegroundColor Yellow

exit 0
