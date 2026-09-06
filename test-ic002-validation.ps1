#!/usr/bin/env powershell
<#
IC-002 Remediation Validation Script
Tests before/after SeSecurityPrivilege grant

Usage:
  # Test current state (pre-remediation)
  .\test-ic002-validation.ps1 -Test Pre

  # After admin grants SeSecurityPrivilege and user logs off/on, test post state
  .\test-ic002-validation.ps1 -Test Post

  # Compare before/after to measure delta
  .\test-ic002-validation.ps1 -Test Delta
#>

param(
  [ValidateSet("Pre", "Post", "Delta")]
  [string]$Test = "Pre"
)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "`n🔬 IC-002 REMEDIATION VALIDATION" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Test Phase: $Test`n"

# File paths for storing results
$preResultFile = "$PSScriptRoot\ic002_pre_validation.json"
$postResultFile = "$PSScriptRoot\ic002_post_validation.json"

function Test-PreRemediation {
  Write-Host "PRE-REMEDIATION STATE TEST" -ForegroundColor Yellow
  Write-Host "-" * 70

  $results = @{}

  # Test 1: Check SeSecurityPrivilege status
  Write-Host "`n[1] Checking SeSecurityPrivilege status..."
  $privCheck = whoami /priv | Select-String "SeSecurityPrivilege"

  if ($privCheck) {
    Write-Host "    ✅ SeSecurityPrivilege FOUND" -ForegroundColor Green
    $results.SeSecurityPrivilegeStatus = "ENABLED"
  } else {
    Write-Host "    ❌ SeSecurityPrivilege NOT FOUND" -ForegroundColor Red
    $results.SeSecurityPrivilegeStatus = "DISABLED"
  }

  # Test 2: Try to access Security Event Log
  Write-Host "`n[2] Testing Security Event Log access..."
  try {
    $events = Get-WinEvent -LogName Security -MaxEvents 1 -ErrorAction Stop
    Write-Host "    ✅ Security log ACCESSIBLE" -ForegroundColor Green
    Write-Host "    Events returned: 1"
    $results.SecurityLogStatus = "ACCESSIBLE"
    $results.SecurityLogEventsCount = 1
  } catch {
    Write-Host "    ❌ Security log BLOCKED" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message.Substring(0, 100))..." -ForegroundColor Red
    $results.SecurityLogStatus = "BLOCKED"
    $results.SecurityLogEventsCount = 0
  }

  # Test 3: Try failedLogons tool equivalent
  Write-Host "`n[3] Testing failed logons query..."
  try {
    $failedLogons = Get-WinEvent -LogName Security -FilterXPath "*[System[EventID=4625]]" -MaxEvents 1 -ErrorAction Stop
    Write-Host "    ✅ Failed logons ACCESSIBLE" -ForegroundColor Green
    $results.FailedLogonsStatus = "ACCESSIBLE"
  } catch {
    Write-Host "    ❌ Failed logons BLOCKED" -ForegroundColor Red
    $results.FailedLogonsStatus = "BLOCKED"
  }

  # Test 4: Try successfulLogons tool equivalent
  Write-Host "`n[4] Testing successful logons query..."
  try {
    $successLogons = Get-WinEvent -LogName Security -FilterXPath "*[System[EventID=4624]]" -MaxEvents 1 -ErrorAction Stop
    Write-Host "    ✅ Successful logons ACCESSIBLE" -ForegroundColor Green
    $results.SuccessfulLogonsStatus = "ACCESSIBLE"
  } catch {
    Write-Host "    ❌ Successful logons BLOCKED" -ForegroundColor Red
    $results.SuccessfulLogonsStatus = "BLOCKED"
  }

  # Calculate visibility percentage
  $accessible = @($results.SecurityLogStatus, $results.FailedLogonsStatus, $results.SuccessfulLogonsStatus) | Where-Object { $_ -eq "ACCESSIBLE" } | Measure-Object | Select-Object -ExpandProperty Count
  $total = 3
  $visibility = [int](($accessible / $total) * 100)

  $results.AuthenticationVisibility = "$visibility%"
  $results.Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

  # Display summary
  Write-Host "`n" -ForegroundColor Yellow
  Write-Host "PRE-REMEDIATION SUMMARY" -ForegroundColor Yellow
  Write-Host "-" * 70
  Write-Host "SeSecurityPrivilege:        $($results.SeSecurityPrivilegeStatus)"
  Write-Host "Security Log Access:        $($results.SecurityLogStatus)"
  Write-Host "Failed Logons Access:       $($results.FailedLogonsStatus)"
  Write-Host "Successful Logons Access:   $($results.SuccessfulLogonsStatus)"

  $visColor = if ($results.AuthenticationVisibility -eq "0%") { "Red" } else { "Green" }
  Write-Host "Authentication Visibility:  $($results.AuthenticationVisibility)" -ForegroundColor $visColor

  # Save results
  $results | ConvertTo-Json | Out-File -FilePath $preResultFile
  Write-Host "`nResults saved to: $preResultFile`n"

  return $results
}

function Test-PostRemediation {
  Write-Host "POST-REMEDIATION STATE TEST" -ForegroundColor Yellow
  Write-Host "-" * 70

  $results = @{}

  # Test 1: Check SeSecurityPrivilege status
  Write-Host "`n[1] Checking SeSecurityPrivilege status..."
  $privCheck = whoami /priv | Select-String "SeSecurityPrivilege"

  if ($privCheck) {
    Write-Host "    ✅ SeSecurityPrivilege ENABLED" -ForegroundColor Green
    $results.SeSecurityPrivilegeStatus = "ENABLED"
  } else {
    Write-Host "    ⚠️  SeSecurityPrivilege STILL DISABLED" -ForegroundColor Yellow
    Write-Host "    Note: Requires new login session after privilege grant" -ForegroundColor Yellow
    $results.SeSecurityPrivilegeStatus = "DISABLED"
  }

  # Test 2: Try to access Security Event Log
  Write-Host "`n[2] Testing Security Event Log access..."
  try {
    $events = Get-WinEvent -LogName Security -MaxEvents 10 -ErrorAction Stop
    Write-Host "    ✅ Security log ACCESSIBLE" -ForegroundColor Green
    Write-Host "    Events returned: $($events.Count)"
    $results.SecurityLogStatus = "ACCESSIBLE"
    $results.SecurityLogEventsCount = $events.Count
  } catch {
    Write-Host "    ❌ Security log STILL BLOCKED" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message.Substring(0, 100))..." -ForegroundColor Red
    $results.SecurityLogStatus = "BLOCKED"
    $results.SecurityLogEventsCount = 0
  }

  # Test 3: Try failedLogons tool equivalent
  Write-Host "`n[3] Testing failed logons query..."
  try {
    $failedLogons = Get-WinEvent -LogName Security -FilterXPath "*[System[EventID=4625]]" -MaxEvents 10 -ErrorAction Stop
    Write-Host "    ✅ Failed logons ACCESSIBLE" -ForegroundColor Green
    Write-Host "    Events found: $($failedLogons.Count)"
    $results.FailedLogonsStatus = "ACCESSIBLE"
  } catch {
    Write-Host "    ❌ Failed logons BLOCKED" -ForegroundColor Red
    $results.FailedLogonsStatus = "BLOCKED"
  }

  # Test 4: Try successfulLogons tool equivalent
  Write-Host "`n[4] Testing successful logons query..."
  try {
    $successLogons = Get-WinEvent -LogName Security -FilterXPath "*[System[EventID=4624]]" -MaxEvents 10 -ErrorAction Stop
    Write-Host "    ✅ Successful logons ACCESSIBLE" -ForegroundColor Green
    Write-Host "    Events found: $($successLogons.Count)"
    $results.SuccessfulLogonsStatus = "ACCESSIBLE"
  } catch {
    Write-Host "    ❌ Successful logons BLOCKED" -ForegroundColor Red
    $results.SuccessfulLogonsStatus = "BLOCKED"
  }

  # Calculate visibility percentage
  $accessible = @($results.SecurityLogStatus, $results.FailedLogonsStatus, $results.SuccessfulLogonsStatus) | Where-Object { $_ -eq "ACCESSIBLE" } | Measure-Object | Select-Object -ExpandProperty Count
  $total = 3
  $visibility = [int](($accessible / $total) * 100)

  $results.AuthenticationVisibility = "$visibility%"
  $results.Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

  # Display summary
  Write-Host "`n" -ForegroundColor Yellow
  Write-Host "POST-REMEDIATION SUMMARY" -ForegroundColor Yellow
  Write-Host "-" * 70
  Write-Host "SeSecurityPrivilege:        $($results.SeSecurityPrivilegeStatus)"
  Write-Host "Security Log Access:        $($results.SecurityLogStatus)"
  Write-Host "Failed Logons Access:       $($results.FailedLogonsStatus)"
  Write-Host "Successful Logons Access:   $($results.SuccessfulLogonsStatus)"

  $visColor = if ($results.AuthenticationVisibility -eq "100%") { "Green" } else { "Yellow" }
  Write-Host "Authentication Visibility:  $($results.AuthenticationVisibility)" -ForegroundColor $visColor

  # Save results
  $results | ConvertTo-Json | Out-File -FilePath $postResultFile
  Write-Host "`nResults saved to: $postResultFile`n"

  return $results
}

function Compare-Delta {
  if (-not (Test-Path $preResultFile)) {
    Write-Host "❌ Pre-remediation results not found. Run with -Test Pre first." -ForegroundColor Red
    return
  }

  if (-not (Test-Path $postResultFile)) {
    Write-Host "❌ Post-remediation results not found. Run with -Test Post first." -ForegroundColor Red
    return
  }

  $pre = Get-Content $preResultFile | ConvertFrom-Json
  $post = Get-Content $postResultFile | ConvertFrom-Json

  Write-Host "DELTA ANALYSIS" -ForegroundColor Yellow
  Write-Host "=" * 70
  Write-Host "`nAuthentication Visibility Delta:" -ForegroundColor Yellow
  Write-Host "  Before (Pre):  $($pre.AuthenticationVisibility)" -ForegroundColor Red
  Write-Host "  After (Post):  $($post.AuthenticationVisibility)" -ForegroundColor Green

  $prePct = [int]$pre.AuthenticationVisibility.TrimEnd('%')
  $postPct = [int]$post.AuthenticationVisibility.TrimEnd('%')
  $delta = $postPct - $prePct

  Write-Host "  Delta:        +$delta% (improvement)"

  Write-Host "`nTool-by-Tool Status:" -ForegroundColor Yellow
  Write-Host "  securityLogs:       $($pre.SecurityLogStatus) -> $($post.SecurityLogStatus)"
  Write-Host "  failedLogons:       $($pre.FailedLogonsStatus) -> $($post.FailedLogonsStatus)"
  Write-Host "  successfulLogons:   $($pre.SuccessfulLogonsStatus) -> $($post.SuccessfulLogonsStatus)"

  if ($delta -eq 100) {
    Write-Host "`n✅ REMEDIATION SUCCESSFUL" -ForegroundColor Green
    Write-Host "   All authentication tools are now functional" -ForegroundColor Green
  } else {
    Write-Host "`n⚠️  REMEDIATION INCOMPLETE" -ForegroundColor Yellow
    Write-Host "   Not all tools are accessible yet" -ForegroundColor Yellow
  }

  Write-Host "`n"
}

# Main execution
switch ($Test) {
  "Pre" { Test-PreRemediation | Out-Null }
  "Post" { Test-PostRemediation | Out-Null }
  "Delta" { Compare-Delta }
}
