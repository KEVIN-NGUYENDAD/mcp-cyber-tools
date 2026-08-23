Write-Host "IC-002 BASELINE TEST"
Write-Host "===================="

$results = @{}

Write-Host "`n[1] SeSecurityPrivilege status"
$priv = whoami /priv | Select-String "SeSecurityPrivilege"
if ($priv) {
  Write-Host "OK: ENABLED"
  $results.SeSecurityPrivilege = "ENABLED"
} else {
  Write-Host "BLOCKED: NOT FOUND"
  $results.SeSecurityPrivilege = "DISABLED"
}

Write-Host "`n[2] Security Event Log access"
try {
  $events = Get-WinEvent -LogName Security -MaxEvents 1 -ErrorAction Stop
  Write-Host "OK: ACCESSIBLE"
  $results.SecurityLog = "ACCESSIBLE"
} catch {
  Write-Host "BLOCKED: Cannot read"
  $results.SecurityLog = "BLOCKED"
}

Write-Host "`n[3] Failed logons (EventID 4625)"
try {
  $events = Get-WinEvent -LogName Security -FilterXPath "*[System[EventID=4625]]" -MaxEvents 1 -ErrorAction Stop
  Write-Host "OK: ACCESSIBLE"
  $results.FailedLogons = "ACCESSIBLE"
} catch {
  Write-Host "BLOCKED: Cannot read"
  $results.FailedLogons = "BLOCKED"
}

Write-Host "`n[4] Successful logons (EventID 4624)"
try {
  $events = Get-WinEvent -LogName Security -FilterXPath "*[System[EventID=4624]]" -MaxEvents 1 -ErrorAction Stop
  Write-Host "OK: ACCESSIBLE"
  $results.SuccessfulLogons = "ACCESSIBLE"
} catch {
  Write-Host "BLOCKED: Cannot read"
  $results.SuccessfulLogons = "BLOCKED"
}

Write-Host "`n========================================`n"
Write-Host "SUMMARY"
$accessible = @($results.SecurityLog, $results.FailedLogons, $results.SuccessfulLogons) | Where-Object { $_ -eq "ACCESSIBLE" } | Measure-Object | Select-Object -ExpandProperty Count
$visibility = [int](($accessible / 3) * 100)

Write-Host "SeSecurityPrivilege: $($results.SeSecurityPrivilege)"
Write-Host "Security Log:        $($results.SecurityLog)"
Write-Host "Failed Logons:       $($results.FailedLogons)"
Write-Host "Successful Logons:   $($results.SuccessfulLogons)"
Write-Host "`nAuthentication Visibility: $visibility%`n"

$results.AuthenticationVisibility = "$visibility%"
$results.Timestamp = (Get-Date).ToString()
$results | ConvertTo-Json | Out-File ic002_pre_validation.json

Write-Host "Results saved to: ic002_pre_validation.json"

if ($visibility -eq 0) {
  Write-Host "`nREMEDIATION REQUIRED: SeSecurityPrivilege not granted"
  Write-Host "Admin action needed: ntrights +r SeSecurityPrivilege -u kevin\tamng"
} else {
  Write-Host "`nVisibility already at: $visibility%"
}
