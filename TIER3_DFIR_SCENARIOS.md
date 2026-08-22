# Tier 3: DFIR Scenario Testing
**Cyber Tools v1.0.2**  
**Date**: 2026-08-22  
**Status**: READY FOR EXECUTION  
**Baseline**: v1.0.2-tier2-complete

---

## 🎯 TIER 3 OBJECTIVE

**Tier 2 Asked**: Is the tool reliable?  
**Tier 3 Asks**: Can an analyst use these tools to investigate a real incident?

Shift from **Tool Verification** → **Investigator Capability Validation**

---

## 🔍 DFIR SCENARIOS (5 Total)

Each scenario tests:
1. **Timeline Integrity** - Events in correct sequence
2. **Evidence Correlation** - Linking data across multiple collectors
3. **Multi-tool Analysis** - Combining data from 3+ tools
4. **Incident Reconstruction** - Building coherent narrative
5. **Chain of Custody** - Maintaining evidence integrity

---

## 🧪 SCENARIO 1: Malware Execution & Persistence

### Incident Profile
```
Attack Vector:    Trojan executable
Timeline:         Known infection point (specific timestamp)
Artifacts:        Process creation, registry persistence, scheduled task
Tools Required:   4+ (processes, registry, scheduled tasks, eventlogs)
```

### Test Procedure

**Step 1: Baseline Collection**
```
runningProcesses     → Capture all processes at T0
registryRunKeys      → Capture HKLM\Software\Microsoft\Windows\CurrentVersion\Run
scheduledTasks       → Capture all scheduled tasks
eventLogs            → Capture Security logs from 1 hour before to now
```

**Step 2: Simulate Infection** (Admin mode)
- Execute known trojan binary
- Observe process creation
- Verify registry key added
- Verify task scheduled

**Step 3: Collect Post-Infection**
```
runningProcesses     → New process visible?
registryRunKeys      → Persistence key visible?
scheduledTasks       → New task visible?
eventLogs            → Creation events logged?
```

**Step 4: Timeline Reconstruction**
```
Question: Can analyst build timeline of:
  14:32:15 - Process created (PID 1234, cmd.exe)
  14:32:22 - Registry key written (Software\Microsoft\Windows\...\Run)
  14:33:01 - Scheduled task registered
  14:33:45 - Event logged
```

**Step 5: Verification Checklist**
- ✅ Events in chronological order?
- ✅ Timestamps consistent across tools?
- ✅ No data loss or truncation?
- ✅ All collectors captured same incident?

**Expected Result**: ✅ PASS if analyst can construct coherent timeline

---

## 🧪 SCENARIO 2: Lateral Movement (Network Reconnaissance)

### Incident Profile
```
Attack Vector:    RDP session from compromised host
Timeline:         Known initial compromise time
Artifacts:        Network connections, auth logs, RDP events
Tools Required:   5+ (network, eventlogs, processes, users, firewall)
```

### Test Procedure

**Step 1: Baseline**
```
activeConnections    → Established TCP connections
successfulLogons     → Recent successful login events
failedLogons         → Failed login attempts (past 24h)
firewallRules        → Inbound rules for RDP
```

**Step 2: Simulate Attack**
- Establish RDP connection from different host
- Authenticate with specific credentials
- Perform reconnaissance commands
- Monitor network activity

**Step 3: Collect Evidence**
```
activeConnections    → RDP connection visible?
successfulLogons     → Login event logged?
powershellLogs       → Commands logged?
processTree          → Process hierarchy shows exploration?
```

**Step 4: Correlation Test**
```
Connect data points:
  Network: 10.0.0.X:XXXXX → RemoteHost:3389 (RDP)
  Logs: User@Domain login at T0
  Process: cmd.exe → powershell.exe → certutil.exe
  Result: "Lateral movement confirmed via RDP + remote execution"
```

**Expected Result**: ✅ PASS if analyst can trace attack path

---

## 🧪 SCENARIO 3: Data Exfiltration Detection

### Incident Profile
```
Attack Vector:    Suspicious file transfer
Timeline:         Unusual network activity
Artifacts:        Large outbound connections, file access, USB activity
Tools Required:   4+ (network, fileMetadata, usbLogs, eventLogs)
```

### Test Procedure

**Step 1: Baseline**
```
outboundRules        → Firewall egress rules
activeConnections    → Established connections
recentFiles          → Recently accessed files
usbLogs              → USB device connections
```

**Step 2: Simulate Exfiltration**
- Create large file in Documents
- Establish connection to external IP (or simulate)
- Monitor file operations
- Check USB device connections

**Step 3: Collect Evidence**
```
activeConnections    → Large file transfer visible?
fileMetadata         → File size/timestamp match suspected exfil?
usbLogs              → USB device connected?
eventLogs            → File access events logged?
```

**Step 4: Analysis Narrative**
```
Timeline reconstruction:
  T0: USB device connected
  T5: File access elevated (Documents\sensitive.xlsx)
  T10: Outbound connection to 1.2.3.4:443 (HTTPS)
  T15: File transfer complete

Conclusion: "Data likely exfiltrated via USB or network"
```

**Expected Result**: ✅ PASS if analyst can identify exfiltration vector

---

## 🧪 SCENARIO 4: Privilege Escalation Investigation

### Incident Profile
```
Attack Vector:    Token impersonation / UAC bypass
Timeline:         Process elevation at known time
Artifacts:        Process creation with elevated privileges, registry changes
Tools Required:   4+ (processes, registry, eventLogs, localAdmins)
```

### Test Procedure

**Step 1: Baseline**
```
processByPid         → Note current process privileges
localAdmins          → Current admin members
registryRunKeys      → Current HKLM run keys
eventLogs            → Security events (4688 - process creation)
```

**Step 2: Simulate Escalation**
- Run process with elevation request
- Observe UAC prompt handling
- Check if new process runs as admin
- Verify registry modifications

**Step 3: Collect Evidence**
```
processByPid         → Process now elevated?
localAdmins          → New admin user added?
registryRunKeys      → Persistence key added?
eventLogs            → Privilege escalation event logged?
```

**Step 4: Attribution**
```
Questions analyst must answer:
  ✅ Which process attempted escalation?
  ✅ What was the execution path?
  ✅ When did escalation occur (timestamp)?
  ✅ Did escalation succeed?
  ✅ What changes resulted?
```

**Expected Result**: ✅ PASS if analyst can attribute escalation

---

## 🧪 SCENARIO 5: Incident Reconstruction (Complex Multi-Step)

### Incident Profile
```
Attack Scenario:  Full attack chain
Timeline:         Initial access → Persistence → Lateral movement → Exfiltration
Tools Required:   7+ (all relevant collectors)
Duration:         30-60 minute investigation
```

### Test Procedure

**Step 1: Initial Compromise Indicators**
```
Hunt for:
  • Unusual process execution (servicesChecker)
  • Registry persistence (registryRunKeys)
  • Scheduled task creation (scheduledTasks)
  • Event log entries (eventLogs, securityLogs)
```

**Step 2: Establish Timeline**
```
For each artifact:
  1. Tool returns data ✅
  2. Timestamp captured ✅
  3. Correlated with other events ✅
  4. Placed on unified timeline ✅
```

**Step 3: Trace Attack Path**
```
Step 1: Initial execution
  → Which process was first compromised?
  → From which location?
  → At what time?

Step 2: Persistence achieved
  → How does malware survive reboot?
  → Registry/scheduled task/service?
  → Verification?

Step 3: Lateral movement
  → Which hosts did attacker access?
  → Authentication method?
  → Command execution method?

Step 4: Data theft
  → What data accessed?
  → When?
  → How exfiltrated?
```

**Step 4: Chain of Custody**
```
Each data point must have:
  ✅ Source tool (which collector)
  ✅ Timestamp (when collected)
  ✅ Integrity (valid JSON, no truncation)
  ✅ Correlation (linked to other evidence)
  ✅ Attribution (analyst can explain it)
```

**Step 5: Final Report**
```
Analyst produces report answering:
  1. Timeline of attack (start to finish)
  2. Attacker actions (sequence of commands/activities)
  3. Compromised systems (which hosts)
  4. Data affected (what was accessed/exfiltrated)
  5. Recommendations (remediation steps)
```

**Expected Result**: ✅ PASS if comprehensive incident reconstruction possible

---

## 📊 TIER 3 PASS CRITERIA

### Per Scenario
```
✅ Timeline Integrity: Events in correct sequence, timestamps consistent
✅ Evidence Correlation: Data from multiple tools correlates logically
✅ Multi-tool Analysis: Analyst can combine ≥3 tools for analysis
✅ Reconstruction: Coherent incident narrative possible
✅ Chain of Custody: All evidence traceable to source tool
```

### Overall Tier 3
```
PASS if:
  ✅ All 5 scenarios completable by analyst
  ✅ 0 data loss or truncation events
  ✅ 0 timestamp inconsistencies
  ✅ 0 correlation failures
  ✅ Evidence maintains integrity throughout
  
FAIL if:
  ❌ Any scenario incomplete
  ❌ Data truncation detected
  ❌ Timeline cannot be established
  ❌ Multi-tool correlation fails
  ❌ Chain of custody broken
```

---

## 📋 TIER 3 EXECUTION TEMPLATE

For each scenario, document:

```markdown
## SCENARIO X: [Name]

### Execution Summary
- Status: [PASS/FAIL]
- Duration: [minutes]
- Tools Used: [count]
- Data Points Collected: [count]

### Timeline Construction
[Analyst's reconstructed timeline]

### Evidence Correlation
[Which tools correlate?]

### Narrative Reconstruction
[Coherent attack story?]

### Issues Encountered
[Any failures, truncations, inconsistencies?]

### Analyst Confidence Level
[1-10: Could analyst testify in court?]

### Notes
[Observations, improvements needed]
```

---

## 🎯 SUCCESS DEFINITION

**Tier 3 Complete when:**

An analyst with no prior knowledge of the testing can:

1. **Collect** evidence using cyber-tools
2. **Correlate** data from multiple collectors
3. **Reconstruct** chronological attack timeline
4. **Identify** attacker TTPs (tactics, techniques, procedures)
5. **Attribute** actions to specific processes/users/hosts
6. **Maintain** chain of custody throughout

All without:
- ❌ Silent failures
- ❌ Data loss
- ❌ Timestamp inconsistencies
- ❌ Correlation breaks

---

## 📅 EXECUTION SCHEDULE

```
2026-08-22: Tier 3 setup & baseline collection
2026-08-25: Scenarios 1-2 execution
2026-08-28: Scenarios 3-4 execution
2026-08-31: Scenario 5 execution (complex)
2026-09-03: Report compilation
2026-09-04: Sign-off & release approval
2026-09-11: v1.0.2 Release
```

---

## 🔐 BASELINE INTEGRITY

**This Tier 3 testing will use:**
- ✅ Code: v1.0.2-tier2-complete (frozen baseline)
- ✅ No new features during Tier 3
- ✅ Bug fixes only if critical (emergency only)
- ✅ All changes tracked against baseline

**Goal**: Isolate Tier 3 failures to either:
1. Tool limitations (not Tier 2 scope)
2. Scenario design issues (not code)
3. Analyst process issues (not code)

---

## 🎓 KEY DIFFERENCE: Tier 2 vs Tier 3

**Tier 2**: Can the tool work?
```
Tool execution → Real data → JSON valid → ✅ Works
```

**Tier 3**: Can the analyst work?
```
Real incident → Use tools → Correlate data → Reconstruct timeline → ✅ Investigates
```

---

**Status**: Ready for Tier 3 DFIR Scenario Testing  
**Baseline**: v1.0.2-tier2-complete (frozen)  
**Next Phase**: Scenario 1 Execution
