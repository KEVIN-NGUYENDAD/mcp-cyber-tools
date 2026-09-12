# PowerShell script to install PM2 as Windows Service
# MUST RUN AS ADMINISTRATOR

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please follow these steps:" -ForegroundColor Yellow
    Write-Host "  1. Right-click on PowerShell" -ForegroundColor White
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor White
    Write-Host "  3. Click 'Yes' on the UAC prompt" -ForegroundColor White
    Write-Host "  4. Run this command:" -ForegroundColor White
    Write-Host "     Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force" -ForegroundColor Cyan
    Write-Host "  5. Then run this script again:" -ForegroundColor White
    Write-Host "     & '$PSScriptRoot\install-pm2-windows-service-admin.ps1'" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

Write-Host "✓ Running with Administrator privileges" -ForegroundColor Green
Write-Host ""

# Set execution policy for this process
Write-Host "Setting execution policy..." -ForegroundColor Cyan
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

Write-Host "✓ Execution policy set" -ForegroundColor Green
Write-Host ""

# Check if PM2 is installed
Write-Host "Checking PM2 installation..." -ForegroundColor Cyan
$pm2Check = & npm list -g pm2 2>&1
if ($pm2Check -match "pm2") {
    Write-Host "✓ PM2 is installed" -ForegroundColor Green
} else {
    Write-Host "ERROR: PM2 is not installed globally" -ForegroundColor Red
    Write-Host "Please install PM2 first: npm install -g pm2" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check if PM2 Windows Service module is installed
Write-Host "Checking pm2-windows-service module..." -ForegroundColor Cyan
$modules = & pm2 module:list 2>&1
if ($modules -match "pm2-windows-service") {
    Write-Host "✓ pm2-windows-service module is installed" -ForegroundColor Green
} else {
    Write-Host "⚠ pm2-windows-service module not installed, installing..." -ForegroundColor Yellow
    & pm2 install pm2-windows-service
    Start-Sleep -Seconds 3
}

Write-Host ""

# List current PM2 processes
Write-Host "Current PM2 processes:" -ForegroundColor Cyan
& pm2 list
Write-Host ""

# Install the Windows service
Write-Host "Installing PM2 as Windows Service..." -ForegroundColor Cyan
Write-Host "(This will create a Windows service that auto-starts PM2 processes on boot)" -ForegroundColor Gray
Write-Host ""

# The pm2-windows-service module should handle the installation
# If it doesn't work, try running this directly:
$pm2ModulePath = "$env:USERPROFILE\.pm2\modules\pm2-windows-service"
if (Test-Path "$pm2ModulePath\node_modules\pm2-windows-service\bin\pm2-service-install.cmd") {
    Write-Host "Running installer from module..." -ForegroundColor Cyan
    & "$pm2ModulePath\node_modules\pm2-windows-service\bin\pm2-service-install.cmd"
} else {
    Write-Host "Module installer not found, attempting alternative method..." -ForegroundColor Yellow
    # Alternative: Use npm to run the module's CLI
    Write-Host "Creating Windows service with NPM..." -ForegroundColor Cyan
    & npm run -g pm2 windows-service-install 2>&1 || Write-Host "Note: NPM script method may not be available" -ForegroundColor Yellow
}

Write-Host ""

# Verify the service was created
Write-Host "Verifying Windows service installation..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

$service = Get-Service -Name "PM2*" -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "✓ Service found!" -ForegroundColor Green
    Write-Host ""
    $service | Format-Table Name, Status, StartType
    Write-Host ""

    if ($service.Status -eq "Stopped") {
        Write-Host "Starting PM2 service..." -ForegroundColor Cyan
        Start-Service -Name $service.Name
        Start-Sleep -Seconds 2
        Get-Service -Name $service.Name
    }
} else {
    Write-Host "❌ Service not created yet" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check PM2 module logs:" -ForegroundColor White
    Write-Host "     Get-Content `$env:USERPROFILE\.pm2\logs\pm2-windows-service-error.log -Tail 20" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. Check if processes are running in PM2:" -ForegroundColor White
    Write-Host "     pm2 list" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  3. Verify PM2 can access Windows:" -ForegroundColor White
    Write-Host "     pm2 show pm2-windows-service" -ForegroundColor Cyan
}

Write-Host ""

# Final status
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Installation Complete" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Verify processes are set to auto-restart:" -ForegroundColor White
Write-Host "     pm2 list" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Save PM2 configuration:" -ForegroundColor White
Write-Host "     pm2 save" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Test auto-start (reboot Windows and verify):" -ForegroundColor White
Write-Host "     Restart-Computer -Force" -ForegroundColor Cyan
Write-Host ""
Write-Host "  4. After reboot, check service status:" -ForegroundColor White
Write-Host "     services.msc (or Get-Service PM2*)" -ForegroundColor Cyan
Write-Host ""

Write-Host "✓ Setup complete!" -ForegroundColor Green
