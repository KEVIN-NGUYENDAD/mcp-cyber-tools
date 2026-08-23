# FIELD TEST PACK

**Real Investigation Scenarios**  
**Exact commands for each scenario**  
**Success criteria for validation**

---

## SCENARIO 1: SUSPICIOUS POWERSHELL INVESTIGATION

**Objective:** Detect suspicious PowerShell execution and trace history

### Tools to Run (in order)

**Step 1: Enumerate running processes**
```powershell
# List all PowerShell processes
Get-Process powershell -ErrorAction SilentlyContinue | Select-Object ProcessName, Id, Handles, Memory

# Expected: Shows all PowerShell processes with memory usage
# Success: ✓ if results show running processes
```

**Step 2: Check event logs for PowerShell history**
```powershell
# Query event logs for PowerShell execution (Event ID 4688)
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4688} -MaxEvents 20 -ErrorAction SilentlyContinue | 
  Select-Object TimeCreated, Message | Format-Table -AutoSize

# Expected: Shows recent PowerShell command execution
# Success: ✓ if results include PowerShell.exe launches
```

**Step 3: Check process details**
```powershell
# Get command-line arguments of running PowerShell
Get-CimInstance Win32_Process -Filter "name='powershell.exe'" -ErrorAction SilentlyContinue | 
  Select-Object ProcessId, CommandLine

# Expected: Shows full command-line with arguments
# Success: ✓ if command-line is complete (not truncated)
```

**Step 4: Check for persistence mechanisms**
```powershell
# Check registry for PowerShell persistence
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Run -ErrorAction SilentlyContinue |
  Select-Object * | Format-List

# Expected: Shows startup registry entries
# Success: ✓ if no suspicious PowerShell entries found
```

### Expected Evidence
- Process execution history
- Full command-line arguments (IC-035 improvement)
- Event log correlations
- No registry-based persistence

### Success Criteria
- [ ] All 4 queries complete without errors
- [ ] Event log returns results (IC-035)
- [ ] Command-line not truncated (IC-041)
- [ ] Investigation completes in <2 minutes

---

## SCENARIO 2: FAILED LOGIN INVESTIGATION

**Objective:** Analyze failed login attempts and identify patterns

### Tools to Run (in order)

**Step 1: Query failed logons**
```powershell
# Failed logon events (Event ID 4625)
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4625} -MaxEvents 50 -ErrorAction SilentlyContinue |
  Select-Object TimeCreated, @{Name="Account";Expression={$_.Properties[5].Value}}, @{Name="Reason";Expression={$_.Properties[8].Value}} |
  Format-Table -AutoSize

# Expected: Shows failed logon attempts with timestamps and accounts
# Success: ✓ if returns results without errors (IC-035)
```

**Step 2: Query successful logons**
```powershell
# Successful logon events (Event ID 4624)
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 50 -ErrorAction SilentlyContinue |
  Select-Object TimeCreated, @{Name="Account";Expression={$_.Properties[5].Value}}, @{Name="LogonType";Expression={$_.Properties[8].Value}} |
  Format-Table -AutoSize

# Expected: Shows successful logins for comparison
# Success: ✓ if returns results without errors (IC-035)
```

**Step 3: Check for brute force patterns**
```powershell
# Get count of failed logons per account (last 100 events)
$failedLogons = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4625} -MaxEvents 100 -ErrorAction SilentlyContinue
$failedLogons | 
  Select-Object @{Name="Account";Expression={$_.Properties[5].Value}} |
  Group-Object Account |
  Sort-Object Count -Descending |
  Select-Object Name, Count

# Expected: Shows accounts with multiple failed logons
# Success: ✓ if suspicious patterns identified
```

**Step 4: Check logged-on users**
```powershell
# Currently logged-on users
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624,4625} -MaxEvents 20 -ErrorAction SilentlyContinue |
  Select-Object TimeCreated, @{Name="Account";Expression={$_.Properties[5].Value}} |
  Sort-Object TimeCreated -Descending

# Expected: Shows active user sessions
# Success: ✓ if results match system expectations
```

### Expected Evidence
- Failed logon timestamps
- Account names
- Logon failure reasons
- Comparison with successful logins
- Brute-force patterns (if any)

### Success Criteria
- [ ] All 4 queries complete without errors
- [ ] Failed logons returned from event log (IC-035)
- [ ] Successful logons returned from event log (IC-035)
- [ ] No syntax errors in hashtable filters (IC-035)
- [ ] Investigation completes in <2 minutes

---

## SCENARIO 3: PERSISTENCE DISCOVERY

**Objective:** Identify all persistence mechanisms on the system

### Tools to Run (in order)

**Step 1: Check startup registry keys**
```powershell
# Startup programs in registry
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Run -ErrorAction SilentlyContinue |
  Select-Object * -ExcludeProperty PS* | Format-Table -AutoSize

# Expected: Shows programs that run at startup (should be cached - IC-036)
# Success: ✓ if returns quickly (< 100ms if cached)
```

**Step 2: Check RunOnce keys**
```powershell
# RunOnce registry keys (run one time then deleted)
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce -ErrorAction SilentlyContinue |
  Select-Object * -ExcludeProperty PS* | Format-Table -AutoSize

# Expected: Shows one-time startup programs
# Success: ✓ if returns quickly (cached - IC-036)
```

**Step 3: Check scheduled tasks**
```powershell
# Suspicious scheduled tasks
Get-ScheduledTask -ErrorAction SilentlyContinue |
  Where-Object {$_.Principal.UserId -eq "SYSTEM" -or $_.Principal.UserId -eq "NT AUTHORITY\SYSTEM"} |
  Select-Object TaskName, State, Principal |
  Format-Table -AutoSize

# Expected: Shows system-level scheduled tasks
# Success: ✓ if complete list returned
```

**Step 4: Check services**
```powershell
# Auto-start services
Get-WmiObject win32_service -Filter "StartMode='Auto'" -ErrorAction SilentlyContinue |
  Select-Object Name, DisplayName, State |
  Format-Table -AutoSize

# Expected: Shows auto-starting services
# Success: ✓ if complete list without errors
```

### Expected Evidence
- Registry Run keys
- RunOnce keys
- Scheduled tasks (system)
- Auto-start services
- All persistence mechanisms documented

### Success Criteria
- [ ] All 4 queries complete without errors
- [ ] Registry queries cached (IC-036 - <100ms)
- [ ] Complete persistence inventory collected
- [ ] Investigation completes in <1 minute (with cache)

---

## SCENARIO 4: UNKNOWN PROCESS INVESTIGATION

**Objective:** Analyze an unknown process and identify its origin

### Tools to Run (in order)

**Step 1: List running processes**
```powershell
# Get all running processes with memory
Get-Process -ErrorAction SilentlyContinue |
  Sort-Object Memory -Descending |
  Select-Object ProcessName, Id, Memory, @{Name="MemoryMB";Expression={[math]::Round($_.Memory/1MB,2)}} |
  Format-Table -AutoSize -Wrap |
  Head -20

# Expected: Shows top memory-consuming processes
# Success: ✓ if all processes listed
```

**Step 2: Get process details for suspicious process**
```powershell
# Detailed info for a specific process (replace PID with actual process ID)
# Example: Get details for first process
Get-Process | Select-Object -First 1 | ForEach-Object {
  Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue |
    Select-Object ProcessId, Name, CommandLine, ExecutablePath, @{Name="FullPath";Expression={$_.ExecutablePath}}
}

# Expected: Shows full command-line and executable path (IC-041 improves this)
# Success: ✓ if command-line is complete (not truncated - IC-041)
```

**Step 3: Check process parent**
```powershell
# Get process tree
Get-Process -ErrorAction SilentlyContinue |
  Select-Object ProcessName, Id, @{Name="ParentProcess";Expression={(Get-Process -Id $_.Id).Parent.ProcessName}} |
  Sort-Object ParentProcess |
  Format-Table -AutoSize |
  Head -20

# Expected: Shows parent-child process relationships
# Success: ✓ if relationships clearly shown
```

**Step 4: Check if process is signed**
```powershell
# Verify process signature
$process = Get-Process | Select-Object -First 1
$sig = Get-AuthenticodeSignature -FilePath $process.Path -ErrorAction SilentlyContinue
$sig | Select-Object SignerCertificate, Status, Path

# Expected: Shows whether executable is digitally signed
# Success: ✓ if signature status is clear (Microsoft vs. Unknown)
```

### Expected Evidence
- Process list with memory usage
- Full command-line arguments (no truncation - IC-041)
- Parent-child relationships
- Digital signature status
- Complete process inventory

### Success Criteria
- [ ] All 4 queries complete without errors
- [ ] Command-line not truncated (IC-041)
- [ ] Full command-line captured including arguments
- [ ] Signature verification successful
- [ ] Investigation completes in <2 minutes

---

## VALIDATION CHECKLIST

After running all 4 scenarios:

### IC-035 (Event Log Standardization)
- [ ] All event log queries returned results
- [ ] No hashtable syntax errors
- [ ] Failed logons returned correctly
- [ ] Successful logons returned correctly
- [ ] Success rate > 95%

### IC-036 (Registry Caching)
- [ ] Registry queries execute
- [ ] Caching detected (second run faster than first)
- [ ] Performance improvement visible
- [ ] Cache invalidation works
- [ ] Speed improvement > 50%

### IC-041 (Reliability)
- [ ] Fallback works on non-admin machines
- [ ] Complete command-lines captured (not truncated)
- [ ] Retry logic engaged when needed
- [ ] Queries complete despite permission issues
- [ ] Success rate > 90%

### Overall Investigation Quality
- [ ] All scenarios complete successfully
- [ ] Total investigation time < 10 minutes
- [ ] No manual errors or retries needed
- [ ] Evidence collected is actionable
- [ ] Patterns and anomalies clearly identified

---

## Next Steps

After all scenarios complete:
1. Run: `node scripts/telemetry-validator.js`
2. Run: `node scripts/benchmark-runner.js`
3. Run: `node scripts/roi-calculator.js`
4. Review: `benchmark-results.json`
5. Review: `telemetry-health-report.json`
6. Review: `roi-analysis.json`
