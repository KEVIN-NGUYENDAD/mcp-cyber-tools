# HOME SOC MCP Server Startup (PowerShell)
# Runs silently in background
# Allows Claude to query live HOME SOC data

$repoPath = Split-Path $MyInvocation.MyCommand.Path
$logPath = Join-Path $repoPath "logs"
$logFile = Join-Path $logPath "mcp-startup.log"

if (!(Test-Path $logPath)) {
    New-Item -ItemType Directory -Path $logPath -Force | Out-Null
}

# Log startup
Add-Content -Path $logFile -Value "[$(Get-Date)] MCP Server starting..."

# Start MCP server process (hidden window, background)
$processParams = @{
    FilePath = "node"
    ArgumentList = "home-soc-mcp-server.js"
    WorkingDirectory = $repoPath
    WindowStyle = "Hidden"
    RedirectStandardOutput = $logFile
    RedirectStandardError = $logFile
    CreateNoWindow = $true
}

try {
    $process = Start-Process @processParams -PassThru
    Add-Content -Path $logFile -Value "[$(Get-Date)] MCP Server PID: $($process.Id)"
    Add-Content -Path $logFile -Value "[$(Get-Date)] MCP Server running"
} catch {
    Add-Content -Path $logFile -Value "[$(Get-Date)] ERROR: $($_.Exception.Message)"
}
