#!/usr/bin/env powershell

Write-Host "`n🔬 IC-002 REMEDIATION VALIDATION" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Pre-Remediation Baseline Test`n"

$results = @{}

Write-Host "[1] Checking SeSecurityPrivilege status..."
$privCheck = whoami /priv | Select-String "SeSecurityPrivilege"
if ($privCheck) {
  Write-Host "    OK: SeSecurityPrivilege FOUND" -ForegroundColor Green
  $results.SeSecurityPrivilegeStatus = "ENABLED"
} else {
  Write-Host "    BLOCKED: SeSecurityPrivilege NOT FOUND" -ForegroundColor Red
  $results.SeSecurityPrivilegeStatus = "DISABLED"
}

Write-Host "`n[2] Testing Security Event Log access..."
try {
  $events = Get-WinEvent -LogName Security -MaxEvents 1 -ErrorAction Stop
  Write-Host "    OK: Security log ACCESSIBLE" -ForegroundColor Green
  $results.SecurityLogStatus = "ACCESSIBLE"
} catch {
  Write-Host "    BLOCKED: $($_.Exception.Message.Substring(0, 80))" -ForegroundColor Red
  $results.SecurityLogStatus = "BLOCKED"
}

Write-Host "`n[3] Testing failed logons query (EventID 4625)..."
try {
  $failedLogons = Get-WinEvent -LogName Security -FilterXPath "*[System[EventID=4625]]" -MaxEvents 1 -ErrorAction Stop
  Write-Host "    OK: Failed logons ACCESSIBLE" -ForegroundColor Green
  $results.FailedLogonsStatus = "ACCESSIBLE"
} catch {
  Write-Host "    BLOCKED: Cannot access" -ForegroundColor Red
  $results.FailedLogonsStatus = "BLOCKED"
}

Write-Host "`n[4] Testing successful logons query (EventID 4624)..."
try {
  $successLogons = Get-WinEvent -LogName Security -FilterXPath "*[System[EventID=4624]]" -MaxEvents 1 -ErrorAction Stop
  Write-Host "    OK: Successful logons ACCESSIBLE" -ForegroundColor Green
  $results.SuccessfulLogonsStatus = "ACCESSIBLE"
} catch {
  Write-Host "    BLOCKED: Cannot access" -ForegroundColor Red
  $results.SuccessfulLogonsStatus = "BLOCKED"
}

Write-Host "`n" -ForegroundColor Yellow
Write-Host "BASELINE SUMMARY" -ForegroundColor Yellow
Write-Host "-" * 70

$accessible = @($results.SecurityLogStatus, $results.FailedLogonsStatus, $results.SuccessfulLogonsStatus) | Where-Object { $_ -eq "ACCESSIBLE" } | Measure-Object | Select-Object -ExpandProperty Count
$visibility = [int](($accessible / 3) * 100)

Write-Host "SeSecurityPrivilege:        $($results.SeSecurityPrivilegeStatus)"
Write-Host "Security Log Access:        $($results.SecurityLogStatus)"
Write-Host "Failed Logons Access:       $($results.FailedLogonsStatus)"
Write-Host "Successful Logons Access:   $($results.SuccessfulLogonsStatus)"
Write-Host "Authentication Visibility:  $visibility%"

$results.AuthenticationVisibility = "$visibility%"
$results.Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Save to JSON
$results | ConvertTo-Json | Out-File -FilePath "$PSScriptRoot\ic002_pre_validation.json"
Write-Host "`nResults saved to: ic002_pre_validation.json`n"

if ($visibility -eq 0) {
  Write-Host "RESULT: Baseline confirmed. User CANNOT access Security logs." -ForegroundColor Red
  Write-Host "`nREMEDIATION NEEDED:" -ForegroundColor Yellow
  Write-Host "  1. Run (in elevated PowerShell session):" -ForegroundColor Yellow
  Write-Host "     ntrights +r SeSecurityPrivilege -u kevin\tamng" -ForegroundColor Yellow
  Write-Host "  2. Log off and log back on" -ForegroundColor Yellow
  Write-Host "  3. Re-run this script to confirm 100% visibility" -ForegroundColor Yellow
} else {
  Write-Host "RESULT: Partial or full visibility already present." -ForegroundColor Green
}

Write-Host ""
