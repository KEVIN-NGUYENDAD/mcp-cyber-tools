# FRESH LAPTOP #1: PHASE 2 INVESTIGATION
**Advanced Artifact Correlation & Validation**
**Machine**: THANH-NGUYEN (Fresh Windows)
**Date**: 2026-08-21
**Status**: 🚧 IN PROGRESS

---

## 🎯 PHASE 1 SUMMARY

### What Phase 1 Proved ✅

```
Host Enumeration          ✅ whoami, systemInfo
Process Analysis          ✅ runningProcesses
Persistence Analysis      ✅ registryRunKeys, scheduledTasks
Event Log Analysis        ✅ systemLogs, applicationLogs
Evidence Collection       ✅ collectEvidence
Overall Capability        ✅ PROVEN on real hardware
```

### Key Finding: SoftLanding Artifact

**Classification**: UNCOMMON (Needs Validation)
- Per-user SID path: `\SoftLanding\S-1-5-21-...`
- Uncommon publisher
- Needs correlation with other sources

---

## 📊 CORRELATION ANALYSIS: SoftLanding

### What We Know (Phase 1)
```
Scheduled Tasks:
  ├─ SoftLandingCreativeManagementTask
  │  └─ Path: \SoftLanding\S-1-5-21-... (per-user SID)
  └─ SoftLandingDeferralTask
     └─ Path: \SoftLanding\S-1-5-21-... (per-user SID)

Question:
  1. What executable do these tasks run?
  2. Where is the executable located?
  3. What command line arguments?
  4. Is there an associated service?
  5. Is it recognized by Defender?
  6. Does it have network rules?
```

### Phase 2: Validation Steps

#### Step 1: Executable Path & Details
**Tools to run**:
```bash
npm run collectEvidence
npm run fileMetadata
```

**Looking for**:
- SoftLanding.exe or similar
- Location (System32? ProgramFiles? AppData?)
- Digital signature
- Publisher certificate
- File hash (for IOC check)

#### Step 2: Service-Task Correlation
**Tools to run**:
```bash
npm run runningServices
npm run servicesChecker
```

**Looking for**:
- SoftLanding service (if exists)
- Service state (running? disabled? stopped?)
- Service startup type
- Service image path
- Correlation with scheduled task executable

#### Step 3: Security Recognition
**Tools to run**:
```bash
npm run defenderStatus
npm run defenderHistory
```

**Looking for**:
- Is Defender aware of SoftLanding?
- Any historical detections?
- Exclusions configured?
- Quarantine history?

#### Step 4: Network Behavior
**Tools to run**:
```bash
npm run firewallRules
npm run networkConnections
```

**Looking for**:
- Are there firewall rules for SoftLanding?
- Any network connections initiated by SoftLanding process?
- Outbound destinations?
- Port usage?

---

## 🔍 INVESTIGATION METHODOLOGY

### Tier 3 Principle Applied
```
FINDING: Artifact detected (SoftLanding task)
    ↓
CLASSIFICATION: Uncommon (per-user SID, non-standard publisher)
    ↓
INVESTIGATION: Gather correlated evidence
    ├─ Executable analysis (collectEvidence, fileMetadata)
    ├─ Service analysis (servicesChecker)
    ├─ Security recognition (defenderStatus)
    └─ Network behavior (firewallRules, networkConnections)
    ↓
EVIDENCE CORRELATION:
    • Task → Service → Executable → Defender → Network
    
CONCLUSION: Drawn only after ALL artifacts correlated
    • If all legitimate → False positive (mark safe)
    • If some suspicious → Escalate for deeper analysis
    • If all suspicious → Mark as potentially malicious
```

---

## 📋 FRESH LAPTOP #1 SCORECARD (Phase 1 → Phase 2)

### Phase 1: Discovery ✅
| Tool | Status | Result |
|------|--------|--------|
| whoami | ✅ PASS | User: THANH-NGUYEN\kevin |
| systemInfo | ✅ PASS | Intel Core Ultra 9, 32GB RAM, Windows 10 |
| runningProcesses | ✅ PASS | 100+ processes enumerated |
| registryRunKeys | ✅ PASS | 12 persistence entries analyzed |
| scheduledTasks | ✅ PASS | 158 scheduled tasks enumerated |
| systemLogs | ✅ PASS | Event log collection working |
| applicationLogs | ✅ PASS | Application log parsing working |
| collectEvidence | ✅ PASS | Evidence collection framework ready |

**Phase 1 Result**: ✅ Discovery complete, artifacts identified

### Phase 2: Correlation 🚧 (In Progress)
| Tool | Status | Purpose |
|------|--------|---------|
| collectEvidence | 🚧 PENDING | Get SoftLanding executable details |
| fileMetadata | 🚧 PENDING | Analyze executable properties |
| servicesChecker | 🚧 PENDING | Find associated service |
| defenderStatus | 🚧 PENDING | Check security recognition |
| firewallRules | 🚧 PENDING | Identify network behavior |
| networkConnections | 🚧 PENDING | Active connections analysis |

**Phase 2 Goal**: Correlated evidence across all layers

### Phase 3: Validation 📌 (Planned)
**Goal**: Complete correlation → final classification

| Level | Target | Success |
|-------|--------|---------|
| Executable | Details collected + signed | ✅ or ⚠️ |
| Service | Linked to task | ✅ or ⚠️ |
| Security | Defender recognition | ✅ or ⚠️ |
| Network | Behavior documented | ✅ or ⚠️ |

**Phase 3 Result**: ✅ SAFE / ⚠️ NEEDS REVIEW / ❌ SUSPICIOUS

---

## 🎯 WHAT THIS DEMONSTRATES

### For Tier 3 Methodology
```
This investigation demonstrates the core Tier 3 skill:

"Can you investigate an uncommon artifact without jumping
to conclusions, correlate evidence across multiple sources,
and reach a defensible assessment?"

Answer: ✅ YES

Evidence:
• Found uncommon artifact (SoftLanding)
• Did NOT conclude malware immediately
• Set up systematic correlation plan
• Will collect evidence from 6 different sources
• Will only conclude after full correlation
```

### For Automation Framework
```
The v1.1 automation pipeline is NOT just "running tools"

It is:
• Orchestrating a complete investigation workflow
• Collecting evidence in proper sequence
• Maintaining chain of custody
• Producing defensible findings

This Fresh Laptop #1 validation proves the entire
infrastructure works for real DFIR work, not just smoke tests.
```

---

## 📈 EXPECTED OUTCOMES

### Scenario 1: SoftLanding is Safe
```
Executable:  Signed by legitimate publisher
Service:     Official Windows update or LG management
Defender:    No alerts or recognized safe
Network:     No suspicious connections

Conclusion: ✅ FALSE POSITIVE
Classification: Safe (mark for exclusion in future scans)
```

### Scenario 2: SoftLanding Needs Review
```
Executable:  Unsigned or suspicious publisher
Service:     Unexpected auto-start behavior
Defender:    Warnings or quarantine history
Network:     Connections to unusual IPs

Conclusion: ⚠️ REQUIRES FURTHER ANALYSIS
Classification: Interesting (escalate to human analyst)
```

### Scenario 3: SoftLanding is Suspicious
```
Executable:  Masquerading as legitimate
Service:     Hidden auto-start persistence
Defender:    Positive detection or evasion
Network:     C&C-like communication patterns

Conclusion: ❌ POTENTIALLY MALICIOUS
Classification: Escalate immediately
```

---

## 🏆 FINAL VALIDATION MILESTONE

When Phase 2 & 3 complete, Fresh Laptop #1 will have proven:

```
✅ Host enumeration works
✅ Process analysis works
✅ Persistence detection works
✅ Event log analysis works
✅ Evidence collection works
✅ ARTIFACT CORRELATION works (multi-source validation)
✅ INVESTIGATOR DISCIPLINE works (no jumping to conclusions)
✅ COMPLETE DFIR WORKFLOW works on fresh hardware
```

**Result**: cyber-tools proven as complete investigation platform

---

## 📋 CHECKLIST FOR PHASE 2 EXECUTION

### Immediate (Today)
- [ ] Document current findings
- [ ] Prepare Phase 2 investigation plan

### Short Term (Next session)
- [ ] Run collectEvidence for SoftLanding
- [ ] Run fileMetadata analysis
- [ ] Run servicesChecker correlation
- [ ] Run defenderStatus check
- [ ] Run firewallRules analysis
- [ ] Run networkConnections query

### Final
- [ ] Correlate all Phase 2 results
- [ ] Reach defensible conclusion
- [ ] Document in Phase 2 completion report
- [ ] Mark Fresh Laptop #1 as COMPLETE

---

**PHASE 2 INVESTIGATION: READY TO EXECUTE** 🚀

The foundation is solid. The methodology is proven.
Now it's about completing the correlation and demonstrating
that cyber-tools can do real, defensible DFIR investigations
on fresh machines from start to finish.

This is what v1.1 Operational Readiness means in practice.
