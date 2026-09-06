# TIER 3 SCENARIO 5: T1 MULTI-PHASE ATTACK SIMULATION
**Complex Incident Reconstruction Test**  
**Date**: 2026-08-21  
**Simulation Time**: 20:39:00 - 20:40:30

---

## 🎯 ATTACK CHAIN SIMULATION

### PHASE 1A: INITIAL ACCESS (20:39:00)

**Attack Vector**: Phishing email with malicious attachment

Evidence Marker:
```
[2026-08-21 20:39:00] Initial Access Event
Delivery Method: Email attachment (malware.exe)
Execution Path: C:\Users\tamng\Downloads\malware.exe
Process: explorer.exe → malware.exe
User Context: Non-admin (initial compromise)
Result: Malware binary executed
```

**Artifact Reference**: ACCESS-001
- Collector: emailLogs / fileAccess
- Timestamp: 2026-08-21 20:39:00
- Detail: Initial malware execution

---

### PHASE 1B: PERSISTENCE (20:39:15 - 20:39:45)

**Multiple Persistence Mechanisms Established**

**Mechanism 1: Registry Run Key**
```
[2026-08-21 20:39:15] Registry Persistence
Location: HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
Entry: SystemService
Value: C:\ProgramData\SystemService.exe
Result: Auto-run on login established
```

**Artifact Reference**: PERSIST-001
- Collector: registryRunKeys
- Timestamp: 2026-08-21 20:39:15
- Classification: Registry persistence

**Mechanism 2: Scheduled Task**
```
[2026-08-21 20:39:30] Scheduled Task Created
Name: Windows Update Manager
Executable: C:\ProgramData\SystemService.exe
Trigger: On logon
Schedule: Every 1 hour
Result: Recurring execution established
```

**Artifact Reference**: PERSIST-002
- Collector: scheduledTasks
- Timestamp: 2026-08-21 20:39:30
- Classification: Task persistence

**Mechanism 3: Startup Link**
```
[2026-08-21 20:39:45] Startup Folder Link
File: System Service.lnk
Target: C:\ProgramData\SystemService.exe
Location: C:\Users\tamng\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
Result: User-level startup persistence
```

**Artifact Reference**: PERSIST-003
- Collector: startupPrograms
- Timestamp: 2026-08-21 20:39:45
- Classification: Startup persistence

---

### PHASE 1C: PRIVILEGE ESCALATION (20:40:00)

**UAC Bypass Attempt**
```
[2026-08-21 20:40:00] Privilege Escalation
Method: Token impersonation via System task
Source: Non-admin (tamng)
Target: SYSTEM (admin context)
Result: Elevated privileges obtained
New Capabilities: HKLM write access, system process creation
```

**Artifact Reference**: ESCALATE-001
- Collector: processContext / tokenInspection
- Timestamp: 2026-08-21 20:40:00
- Classification: Privilege escalation event

---

### PHASE 1D: LATERAL MOVEMENT (20:40:15)

**Network Reconnaissance + Remote Access**
```
[2026-08-21 20:40:15] Lateral Movement Initiated
Stage 1 - Reconnaissance:
  Command: ipconfig /all (network enumeration)
  Command: net user (account enumeration)
  Result: Target network/users identified

Stage 2 - Remote Access:
  Target: 192.168.1.50 (remote host)
  Method: RDP
  Credentials: Stolen admin account
  Result: Remote desktop session established
```

**Artifact Reference**: LATERAL-001
- Collector: processLogs / networkActivity
- Timestamp: 2026-08-21 20:40:15
- Classification: Lateral movement

---

### PHASE 1E: EXFILTRATION (20:40:30)

**Data Staging + Network Upload**
```
[2026-08-21 20:40:30] Exfiltration Phase
Stage 1 - Data Discovery:
  Location: C:\Users\tamng\Documents\SensitiveData
  Files Found: 3 sensitive files
  Total Size: 424 bytes

Stage 2 - Data Staging:
  Destination: C:\ProgramData\Staging
  Files Copied: 3 (financial, customer, employee records)
  Integrity: Complete (no truncation)

Stage 3 - Network Upload:
  Destination: attacker.com (185.220.100.50:443)
  Protocol: HTTPS
  Status: Upload initiated and completed
```

**Artifact References**: 
- EXFIL-001 (Data discovery)
- EXFIL-002 (File staging)
- EXFIL-003 (Network upload)
- Collector: fileAccess / networkLogs
- Timestamp: 2026-08-21 20:40:30
- Classification: Data exfiltration

---

## 📊 ATTACK TIMELINE SUMMARY

```
20:39:00 - Initial Access (ACCESS-001)
  Phishing attachment executed
  
20:39:15 - Persistence (PERSIST-001)
  Registry Run key created
  
20:39:30 - Persistence (PERSIST-002)
  Scheduled task registered
  
20:39:45 - Persistence (PERSIST-003)
  Startup link created
  
20:40:00 - Privilege Escalation (ESCALATE-001)
  UAC bypass successful, admin context gained
  
20:40:15 - Lateral Movement (LATERAL-001)
  Reconnaissance + RDP connection
  
20:40:30 - Exfiltration (EXFIL-001, 002, 003)
  Data discovered, staged, and uploaded
  
Total Attack Duration: 90 seconds (1.5 minutes)
```

---

## 🎯 ARTIFACTS TO BE EXTRACTED (T3 Phase)

### Expected Artifact Classes:

**ACCESS Class** (Initial Compromise):
- ACCESS-001: Phishing delivery + malware execution

**PERSIST Class** (Persistence Mechanisms):
- PERSIST-001: Registry Run key
- PERSIST-002: Scheduled task
- PERSIST-003: Startup link

**ESCALATE Class** (Privilege Escalation):
- ESCALATE-001: UAC bypass / token elevation

**LATERAL Class** (Lateral Movement):
- LATERAL-001: Network recon + RDP access

**EXFIL Class** (Data Exfiltration):
- EXFIL-001: Data discovery
- EXFIL-002: File staging
- EXFIL-003: Network upload

**Total Expected**: 10 artifacts across 5 attack phases

---

## 🔗 CORRELATION REQUIREMENT FOR SCENARIO 5 PASS

**Single Artifact ≠ Finding**

Example:
```
PERSIST-001 alone = "Registry key exists"
NOT sufficient to conclude persistence
```

**Multi-Artifact Chain = Defensible Finding**

Example:
```
ACCESS-001
├─ Malware executed
├─ Timestamp: 20:39:00

PERSIST-001 ─┐
PERSIST-002 ─├─ Same malware executable path
PERSIST-003 ─┘
├─ Timestamps: 20:39:15 → 20:39:45
├─ All reference C:\ProgramData\SystemService.exe

ESCALATE-001
├─ Admin context achieved
├─ Timestamp: 20:40:00

Result:
"Malware established multi-vector persistence and escalated privileges"
= DEFENSIBLE FINDING (corroborated across 7 artifacts)
```

---

## ⏳ SCENARIO 5 READINESS

```
T0: Baseline Collection        ✅ COMPLETE
T1: Multi-Phase Simulation     ✅ COMPLETE (10 artifacts staged)
T2: Post-Attack Collection     ⏳ READY TO EXECUTE
T3: Artifact Extraction        ⏳ PENDING (10 artifacts to extract)
Correlation Analysis           ⏳ PENDING (5-phase correlation)
Timeline Integration           ⏳ PENDING (90-second attack chain)
Peer Validation               ⏳ PENDING
PASS Determination            ⏳ BLOCKED UNTIL ALL ABOVE COMPLETE
```

---

## 🎓 SCENARIO 5: THE CAPSTONE TEST

Scenario 5 tests investigator's ability to:
1. ✅ Identify 5 distinct attack phases
2. ✅ Extract 10 correlated artifacts
3. ✅ Reconstruct 90-second attack chain
4. ✅ Prove causality across phases
5. ✅ Defend narrative to peer review

Success = Full attack chain reconstruction with peer-validated findings

Failure = Any phase breaks down or peer validation fails

---

**Scenario 5 T1 Simulation: ✅ COMPLETE**

10 artifacts staged across 5 attack phases.
Ready for T2 evidence collection phase.

Status: NOT PASS until artifacts extracted, correlated, and peer-validated.
