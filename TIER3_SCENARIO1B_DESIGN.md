# TIER 3 SCENARIO 1B: MALWARE PERSISTENCE DETECTION
**Cyber Tools v1.0.2 DFIR Capability Test**  
**Date**: 2026-08-22+  
**Status**: 🔧 DESIGN PHASE

---

## 🎯 SCENARIO 1B OBJECTIVE

**Test Question**: Can an analyst detect and identify actual malware persistence when it exists?

**Investigation Type**: Active Threat Detection (Persistence Present)

**Key Difference from 1A**:
- Scenario 1A: Clean system (analyst must correctly identify "no threat")
- Scenario 1B: Compromised system (analyst must correctly identify persistence)

---

## 🔧 CONTROLLED PERSISTENCE CREATION

### Artifact Set 1: Registry Persistence

**Action**: Create registry Run key pointing to malware executable

```powershell
# Create test executable path (harmless marker, not real malware)
$malwarePath = "C:\Users\Public\AppData\Local\WindowsUpdate.exe"

# Create registry persistence entry
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" `
  -Name "WindowsUpdateHelper" `
  -Value $malwarePath
```

**Expected Artifact**:
```
REG-001 (NEW - not in baseline)
├─ Type: Persistence
├─ Key: HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run\WindowsUpdateHelper
├─ Value: C:\Users\Public\AppData\Local\WindowsUpdate.exe
├─ Timestamp: 2026-08-22 [T1+]
├─ Collector: registryRunKeys
└─ Significance: Suspicious - Persistence mechanism
```

---

### Artifact Set 2: Scheduled Task Persistence

**Action**: Create scheduled task that "executes" the malware

```powershell
# Create scheduled task that runs malware executable daily
$taskName = "Windows System Maintenance"
$taskPath = "\System32\"
$action = New-ScheduledTaskAction -Execute $malwarePath
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger
```

**Expected Artifact**:
```
TASK-001 (NEW - not in baseline)
├─ Type: Persistence
├─ Name: Windows System Maintenance
├─ Path: \System32\
├─ Executable: C:\Users\Public\AppData\Local\WindowsUpdate.exe
├─ Trigger: AtStartup (persistence across reboots)
├─ Timestamp: 2026-08-22 [T1+]
├─ Collector: scheduledTasks
└─ Significance: Suspicious - Startup persistence
```

---

### Artifact Set 3: Startup Folder Persistence

**Action**: Create shortcut in Startup folder

```powershell
# Create shortcut in Startup folder
$startupPath = "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
$shortcutPath = "$startupPath\WindowsUpdate.lnk"

# Create .lnk file pointing to malware
# (Using Windows Script Host or similar)
```

**Expected Artifact**:
```
START-001 (NEW - not in baseline)
├─ Type: Persistence
├─ Name: WindowsUpdate.lnk
├─ Target: C:\Users\Public\AppData\Local\WindowsUpdate.exe
├─ Location: C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup
├─ Timestamp: 2026-08-22 [T1+]
├─ Collector: startupPrograms
└─ Significance: Suspicious - Startup link
```

---

## 📊 INVESTIGATION TIMELINE

### T0: Baseline (2026-08-22 09:00:00)
```
Action: Collect baseline state
Collectors: All 6 (as in Scenario 1A)
Expected: Clean system (no persistence)
```

### T1: Simulate Infection (2026-08-22 09:15:00)
```
Action: Create controlled persistence artifacts
├─ REG-001: Registry Run key
├─ TASK-001: Scheduled task
└─ START-001: Startup shortcut

Method: PowerShell script (documented and controlled)
Status: Persistence created with full documentation
```

### T2: Post-Infection Collection (2026-08-22 09:30:00)
```
Action: Collect evidence after persistence creation
Collectors: All 6
Expected: Evidence of new persistence artifacts
```

### T3: Analyst Investigation (2026-08-22 09:45+)
```
Action: Artifact extraction and analysis
Question: Can analyst identify the three new artifacts?
Expected: Yes - clear evidence of persistence
```

---

## 🧪 INVESTIGATION VALIDATION QUESTIONS

### Question 1: Can analyst identify REG-001?
```
Acceptance Criteria:
  ✅ Identified "WindowsUpdateHelper" registry entry
  ✅ Noted path: C:\Users\Public\AppData\Local\WindowsUpdate.exe
  ✅ Classified as: Suspicious (non-standard location)
  ✅ Identified as: Persistence mechanism
```

### Question 2: Can analyst identify TASK-001?
```
Acceptance Criteria:
  ✅ Identified "Windows System Maintenance" task
  ✅ Noted execution: AtStartup
  ✅ Noted executable: C:\Users\Public\AppData\Local\WindowsUpdate.exe
  ✅ Classified as: Suspicious (vague name, suspicious executable)
  ✅ Identified as: Persistence mechanism
```

### Question 3: Can analyst identify START-001?
```
Acceptance Criteria:
  ✅ Identified "WindowsUpdate.lnk" in Startup folder
  ✅ Noted target: C:\Users\Public\AppData\Local\WindowsUpdate.exe
  ✅ Classified as: Suspicious (mimics system binary name)
  ✅ Identified as: Persistence mechanism
```

### Question 4: Can analyst correlate artifacts?
```
Acceptance Criteria:
  ✅ All three artifacts point to same executable
  ✅ All three artifacts created at same time (T1)
  ✅ All three artifacts use similar obfuscation (system-like names)
  ✅ Conclusion: Multi-vector persistence confirmed
```

### Question 5: Is timeline coherent?
```
Acceptance Criteria:
  ✅ T0: Baseline shows clean system (no artifacts)
  ✅ T1: Persistence created (timestamp recorded)
  ✅ T2: Collection shows 3 new artifacts
  ✅ Delta analysis: T0 → T2 reveals exactly what changed
  ✅ Narrative: "Three new persistence mechanisms detected"
```

---

## 📋 ARTIFACT MATRIX TEMPLATE (Scenario 1B)

| Artifact ID | Type | Name | Path | Value | T0 | T2 | Status | Significance |
|-------------|------|------|------|-------|----|----|--------|--------------|
| REG-001 | Persistence | WindowsUpdateHelper | HKLM\...\Run | C:\Users\Public\...\WindowsUpdate.exe | ❌ | ✅ | **NEW** | Registry persistence |
| TASK-001 | Persistence | Windows System Maint. | \System32\ | WindowsUpdate.exe | ❌ | ✅ | **NEW** | Startup persistence |
| START-001 | Persistence | WindowsUpdate.lnk | Startup folder | C:\Users\Public\...\WindowsUpdate.exe | ❌ | ✅ | **NEW** | Startup persistence |
| REG-[SYSTEM] | System | SecurityHealth | HKLM\...\Run | C:\WINDOWS\sys32\... | ✅ | ✅ | EXISTING | Legitimate |
| TASK-[SYSTEM] | System | Adobe Acrobat Update | \ | ... | ✅ | ✅ | EXISTING | Legitimate |
| START-[SYSTEM] | System | McAfee Security | Startup | McAfee.lnk | ✅ | ✅ | EXISTING | Legitimate |

---

## 🎯 SCENARIO 1B SUCCESS CRITERIA

### Minimum Pass Threshold
```
Analyst must identify:
  ✅ At least 2 of 3 malicious artifacts (REG-001, TASK-001, START-001)
  ✅ Correct classification (persistence mechanism)
  ✅ Correct concern level (suspicious/high priority)
  ✅ Coherent timeline connecting artifacts
```

### Maximum Pass Threshold
```
Analyst must identify:
  ✅ All 3 malicious artifacts
  ✅ Correct paths and values
  ✅ Multi-vector correlation (all point to same executable)
  ✅ Proper timeline (T0 clean → T1 infection → T2 detection)
  ✅ Defensible narrative (evidence supports "persistence established")
```

---

## 🔐 CONTROLLED ENVIRONMENT

### Safety Measures
```
✅ No actual malware (using harmless marker executable)
✅ No real harm to system (persistence can be easily removed)
✅ Non-admin execution where possible
✅ Full documentation of what was created
✅ Easy cleanup (remove registry key, task, startup link)
```

### Documentation Requirements
```
✅ T0 baseline collection documented
✅ T1 artifacts created with timestamps
✅ T1 artifact creation method documented
✅ T2 collection performed
✅ All evidence preserved for analysis
```

---

## 📈 EXPECTED DIFFERENCE: 1A vs 1B

### Scenario 1A: Clean System Investigation
```
Finding: No malicious artifacts
Investigator Skill: Correctly identified clean system
Result: ✅ PASS (Professional skepticism + accurate analysis)
```

### Scenario 1B: Persistence Detection
```
Finding: 3 malicious artifacts identified
Investigator Skill: Correctly identified actual persistence
Result: ✅ PASS (Detection capability + threat recognition)
```

---

## 🚀 NEXT STEP

**Status**: Design complete, ready for execution

**When to Run**: After Scenario 1A sign-off

**Expected Timeline**:
- T0 Collection: 2026-08-22 09:00:00
- T1 Persistence Creation: 2026-08-22 09:15:00
- T2 Collection: 2026-08-22 09:30:00
- T3 Analysis: 2026-08-22 10:00+

**Approval Needed**: ✅ Ready to proceed

---

**Scenario 1B is designed to test the next level of investigator capability: not just determining whether system is clean, but detecting and analyzing actual threats when present.**
