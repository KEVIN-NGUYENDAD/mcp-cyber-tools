# TIER 3 SCENARIO 1 EXECUTION: Malware Execution & Persistence
**Cyber Tools v1.0.2 DFIR Investigation**  
**Scenario Date**: 2026-08-21  
**Baseline Time (T0)**: 2026-08-21 19:45:31.355  
**Status**: IN PROGRESS

---

## 🎯 SCENARIO OBJECTIVE

**Test Question**: Can an analyst investigate a malware infection using cyber-tools?

**Scenario Profile**:
- **Attack Vector**: Trojan executable execution
- **Persistence Method**: Registry key + Scheduled task
- **Timeline**: Known infection point
- **Artifacts**: Process creation, registry modification, task registration, event logs
- **Tools Required**: 4+ collectors (processes, registry, tasks, eventlogs)

---

## 📊 PHASE 1: BASELINE COLLECTION (T0)

### 2026-08-21 19:45:31.355

**Baseline Purpose**: Establish clean system state before infection

**Collectors Used**:
1. ✅ runningProcesses
   - Result: 20 top processes by WorkingSet
   - Sample: msedgewebview2, claude browser processes, MsMpEng (Windows Defender)

2. ✅ registryRunKeys (HKLM)
   - Result: Current HKLM\Software\Microsoft\Windows\CurrentVersion\Run entries
   - Baseline registry state captured

3. ✅ scheduledTasks
   - Result: All current scheduled tasks enumerated
   - Baseline task state captured
   - Sample tasks: Adobe updates, NVIDIA drivers, Windows maintenance, etc.

4. ⚠️ eventLogs (Security)
   - Result: FAILED - UnauthorizedAccessException
   - Expected: Non-admin user cannot read Security logs
   - Analyst Note: "This is expected behavior, not a bug"

### Baseline Summary
```
✅ Processes: Captured
✅ Registry: Captured
✅ Tasks: Captured
⚠️ Event Logs: Permission denied (expected, non-admin)
```

---

## 📌 PHASE 2: SIMULATE MALWARE EXECUTION (T1)

### 2026-08-21 19:45:32.xxx

**Simulation Purpose**: Create realistic malware artifacts for detection

**Marker Created**:
```
File: C:\Users\tamng\AppData\Local\Temp\TIER3_SCENARIO1_MARKER_405692074.txt
Timestamp: 2026-08-21 19:45:32 (T1)
Purpose: Simulates malware binary execution
```

**Simulated Actions** (in realistic scenario):
1. Malware binary executes (cmd.exe → powershell.exe)
2. Creates registry persistence key
3. Registers scheduled task for recurring execution
4. System event logs creation event

**Next Step**: Collect post-infection evidence (T2)

---

## 🔍 PHASE 3: POST-INFECTION EVIDENCE COLLECTION (T2)

### Collectors to Run

1. **runningProcesses** (limit=50)
   - Question: Are new processes visible?
   - Expected: Malware process (if still running) visible in list

2. **registryRunKeys** (HKLM)
   - Question: New registry key added?
   - Expected: Persistence key visible (Software\Microsoft\...\Run\[malware])

3. **scheduledTasks**
   - Question: New task registered?
   - Expected: New task visible in list (usually named innocuously)

4. **eventLogs** (if admin)
   - Question: Creation events logged?
   - Expected: Event IDs showing process/registry/task creation

---

## ⏱️ TIMELINE RECONSTRUCTION (Analyst Perspective)

### What Analyst Must Determine

**Question 1**: When did malware first execute?
```
Evidence Path:
  → Registry key creation time
  → Task registration time
  → Process creation timestamp
  → First event log entry
  
Expected Answer: T1 timestamp unified across collectors
```

**Question 2**: What is the malware's execution path?
```
Evidence Path:
  → Process name & ID
  → Executable path location
  → Parent process (how it was launched)
  
Expected Answer: Clear chain (e.g., explorer.exe → cmd.exe → powershell.exe)
```

**Question 3**: How does malware achieve persistence?
```
Evidence Path:
  → Registry key location & value
  → Scheduled task details
  → Startup folder contents
  
Expected Answer: Multiple persistence mechanisms identified
```

**Question 4**: Can analyst prove this is malicious?
```
Evidence Path:
  → Suspicious registry location
  → Suspicious task name/schedule
  → Process execution timing
  
Expected Answer: Analyst can build attribution case
```

---

## 📋 ANALYST WORKFLOW TEST

### Can Analyst Complete These Steps?

- [ ] Step 1: Collect baseline state (T0)
- [ ] Step 2: Identify what changed (T0 → T1)
- [ ] Step 3: Determine infection timestamp
- [ ] Step 4: Trace execution chain
- [ ] Step 5: Identify persistence mechanism
- [ ] Step 6: Build timeline narrative
- [ ] Step 7: Maintain chain of custody
- [ ] Step 8: Document findings

### Success Criteria

✅ PASS if analyst can:
1. **Collect** evidence from 3+ tools
2. **Correlate** data points into timeline
3. **Reconstruct** attack sequence with timestamps
4. **Identify** persistence mechanism
5. **Attribute** actions to specific process
6. **Maintain** evidence traceability

❌ FAIL if:
- Data truncation occurs
- Timestamps inconsistent
- Silent failures prevent collection
- Correlation impossible
- Timeline cannot be established

---

## 📊 TEST EXECUTION DATA

### Baseline Collections (T0: 2026-08-21 19:45:31.355)

**runningProcesses**
```
Record Count: 20
Payload Size: 8.73 KB
Sample Process: msedgewebview2 (PID 60488)
Status: ✅ JSON valid
```

**registryRunKeys**
```
Registry Hive: HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
Entries Found: 1+
Status: ✅ Captured
```

**scheduledTasks**
```
Total Tasks: 300+
Sample: Adobe Acrobat Update, NVIDIA updates, Windows maintenance
Status: ✅ JSON valid
```

**eventLogs (Security)**
```
Status: ⚠️ FAILED - UnauthorizedAccessException
Reason: Non-admin user (expected, not a bug)
```

---

## 🎯 ANALYST INVESTIGATION NARRATIVE

### Timeline That Analyst Must Build

```
2026-08-21 19:45:31 (T0)
  ├─ Baseline collection completed
  ├─ Process list: 20 processes
  ├─ Registry: Current run keys documented
  └─ Tasks: Current scheduled tasks documented

2026-08-21 19:45:32 (T1) - INFECTION EVENT
  ├─ Malware marker file created
  ├─ Event: Simulated process execution
  ├─ Action: Registry key written
  └─ Action: Scheduled task registered

2026-08-21 19:45:3X (T2+) - POST-INFECTION COLLECTION
  ├─ Collect running processes
  ├─ Scan registry for new keys
  ├─ Check scheduled tasks for additions
  └─ Compare T1 → T2 to identify changes

Analysis Questions Analyst Must Answer:
  ✅ Which process is malware?
  ✅ When did it first run?
  ✅ How does it persist?
  ✅ What is the full execution chain?
  ✅ Can we trace from initial execution to persistence?
```

---

## ✅ VERIFICATION CHECKLIST

### Data Integrity
- [ ] All JSON responses valid
- [ ] No truncation detected
- [ ] Timestamps consistent across tools
- [ ] Payload sizes within expected range
- [ ] No silent failures
- [ ] Clear error messages (if any)

### Analyst Capability
- [ ] Can identify baseline vs post-infection
- [ ] Can establish timeline
- [ ] Can correlate multi-tool data
- [ ] Can build narrative
- [ ] Can maintain chain of custody
- [ ] Can attribute malware to process

### Tool Performance
- [ ] Execution time < 2 seconds per tool
- [ ] Memory usage stable
- [ ] No crashes or hangs
- [ ] Error handling clear
- [ ] Output format consistent

---

## 🚀 NEXT STEPS

1. **Await Post-Infection Collection** (T2)
   - Run collectors again with same parameters
   - Compare baseline vs post-infection

2. **Timeline Reconstruction**
   - Build chronological narrative
   - Correlate evidence from multiple tools
   - Identify persistence mechanism

3. **Analyst Verification**
   - Can analyst complete investigation?
   - Is evidence chain intact?
   - Can findings be documented?

4. **Scenario Result**
   - PASS: If analyst can investigate & attribute
   - FAIL: If data loss/corruption/inconsistency

---

## 📝 SCENARIO STATUS

```
Status:         IN PROGRESS
Phase:          1 of 3 (Baseline collected)
Next Action:    Post-infection collection (T2)
Timeline:       2026-08-21 onwards
Confidence:     HIGH (baseline successfully collected)
```

---

**Scenario 1 Execution Document**  
Ready for post-infection testing phase.
